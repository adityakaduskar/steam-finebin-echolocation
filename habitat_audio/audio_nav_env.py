"""Gym environment for audio-goal navigation: Habitat-sim supplies geometry, navmesh and agent motion;
Steam Audio (patched core, sample-accurate sparse reconstruction) supplies the acoustics every step.

Observation: SoundSpaces-style binaural spectrogram of a 1 s source clip convolved with the binaural room impulse
response at the agent's current pose (direct path + reflections, occlusion, air absorption), plus optional rgb/depth.
Actions: 0 stop, 1 move_forward (0.25 m), 2 turn_left (10 deg), 3 turn_right. Reward: SoundSpaces AudioNav shaping.
"""
import os, sys, math, glob, time
# the patched libphonon reads these at load time; they must be set before the first Context is created
AUDIO_SR = 24000                                   # Steam Audio's default HRTF accepts 24 / 44.1 / 48 kHz, not 16 kHz
os.environ.setdefault("STEAMAUDIO_BIN_DURATION", repr(1.0 / AUDIO_SR))
os.environ.setdefault("STEAMAUDIO_RECONSTRUCTION", "sparse")
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
from pysteamaudio import steamaudio as sa
import numpy as np
import gym
from gym import spaces
import habitat_sim
import soundfile as sf
import librosa
from scipy.signal import fftconvolve, resample_poly
from skimage.measure import block_reduce
from .scene_mesh import load_scene_mesh

SS_SR = 16000                                      # SoundSpaces RIR / clip sampling rate used for the spectrogram
STOP, MOVE_FORWARD, TURN_LEFT, TURN_RIGHT = 0, 1, 2, 3
ACTION_NAMES = {MOVE_FORWARD: "move_forward", TURN_LEFT: "turn_left", TURN_RIGHT: "turn_right"}
N3D = math.sqrt(3.0)

ECHO_SECONDS = 0.128                               # echo window: 128 ms = 21.8 m of round trip
def compute_echo_spectrogram(rir_2ch):
    """binaural echo response of a click (= the binaural RIR, 16 kHz) -> |STFT| n_fft 128, hop 16 (1 ms) over the first 128 ms,
    2x mean pooling in time, log1p -> (65, 64, 2). Each frame is 2 ms = 34 cm of round trip."""
    n = int(ECHO_SECONDS * SS_SR); x = rir_2ch[:, :n]
    def stft(v):
        s = np.abs(librosa.stft(v, n_fft=128, hop_length=16, win_length=64, center=True))[:, :n // 16]; return block_reduce(s, block_size=(1, 2), func=np.mean)
    return np.stack([np.log1p(stft(x[0])), np.log1p(stft(x[1]))], axis=-1).astype(np.float32)

SONAR_BINS = (64, 32)                              # range bins (2 ms = 17 cm of range each, 0-10.9 m) x azimuth bins (11.25 deg, full circle)
def compute_sonar(ir, ahead, up, sr=AUDIO_SR, bins=SONAR_BINS, seconds=ECHO_SECONDS, gain=10.0):
    """First-order ambisonic click response (4, samples; ACN/N3D, world frame; sparse reconstruction = one arrival per sample) ->
    range x azimuth 'sonar image' in the body frame. Each sample is an arrival with amplitude |W| and direction (X, Y, Z) / (sqrt(3) W)
    (an acoustic intensity vector). Channel 0 = log1p(gain * summed horizontal amplitude, |W| cos(elevation)) per (range, azimuth) cell;
    azimuth column na/2 = ahead, increasing to the left, wrapping over the full circle (column 0 = behind). Channel 1 = the vertical
    amplitude |W| sin(elevation) (+ = from above), signed log-compressed, so floor and ceiling returns land here rather than in the
    azimuth map. Returns (range_bins, az_bins, 2) float32."""
    nr, na = bins; n = min(int(seconds * sr), ir.shape[1]); W = ir[0, :n]
    right = np.cross(ahead, up)
    dx, dy, dz = -ir[1, :n], ir[2, :n], -ir[3, :n]            # = sqrt(3) * W * (world direction of arrival)
    fwd = dx * ahead[0] + dy * ahead[1] + dz * ahead[2]; rgt = dx * right[0] + dy * right[1] + dz * right[2]; upc = dx * up[0] + dy * up[1] + dz * up[2]
    m = np.abs(W) > 1e-12; idx = np.flatnonzero(m); amp = np.abs(W[m]); sg = np.sign(W[m])
    az = np.arctan2(-rgt[m] * sg, fwd[m] * sg)                # + = left; multiplying by sign(W) cancels the pseudo-random polarity of dense bins
    el = np.clip(upc[m] / (N3D * W[m]), -1.0, 1.0)
    ia = np.clip(np.floor((az + np.pi) / (2 * np.pi) * na).astype(int), 0, na - 1); it = np.minimum((idx * nr) // n, nr - 1)
    img = np.zeros((nr, na)); img_el = np.zeros((nr, na))
    np.add.at(img, (it, ia), amp * np.sqrt(1.0 - el * el)); np.add.at(img_el, (it, ia), amp * el)
    return np.stack([np.log1p(gain * img), np.sign(img_el) * np.log1p(gain * np.abs(img_el))], -1).astype(np.float32)

def compute_spectrogram(audio_2ch):
    """SoundSpaces AudioGoalSensor.compute_spectrogram: |STFT| (n_fft 512, hop 160, win 400), 4x4 mean pooling, log1p -> (F, T, 2)"""
    def stft(x):
        s = np.abs(librosa.stft(x, n_fft=512, hop_length=160, win_length=400)); return block_reduce(s, block_size=(4, 4), func=np.mean)
    return np.stack([np.log1p(stft(audio_2ch[0])), np.log1p(stft(audio_2ch[1]))], axis=-1).astype(np.float32)

def quat_to_ahead_up(q):
    """habitat agent rotation (quaternion w,x,y,z) -> forward (-z) and up (+y) unit vectors in world"""
    w, x, y, z = q.w, q.x, q.y, q.z
    R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    return R @ np.array([0, 0, -1.0]), R @ np.array([0, 1.0, 0])


class SteamAudioNavEnv(gym.Env):
    metadata = {"render.modes": []}

    def __init__(self, scene_glb, sounds_dir=os.path.expanduser("~/sound-spaces/data/sounds/1s_all"), sounds=("telephone.wav",),
                 rgb=False, depth=False, image_size=128, step_size=0.25, turn_angle=10.0, success_distance=1.0, max_steps=500,
                 geodesic_range=(1.0, 15.0), agent_height=1.5, material=("generic", (0.10, 0.20, 0.30), 0.05, (0.100, 0.050, 0.030)),
                 rays=16384, bounces=12, ir_duration=0.5, ambisonic_order=1, air_absorption=True, slack_reward=-0.01,
                 success_reward=10.0, lib_path=None, seed=0, threads=8,
                 goal_sound=True, self_click=False, pointgoal=False, sliding=True, click_gain=1.0, collision_penalty=0.0,
                 scan_angles=None, click_dipole=(0.0, 1.0), explore=False, contact=False, coverage_cell=0.5, coverage_reward=1.0,
                 aux_directions=None, aux_max_range=10.0, echo_obs="spectrogram", beams=None, click_cost=0.0, sonar_bins=SONAR_BINS, echo_dropout=0.0):
        """echo_obs: 'spectrogram' = binaural echo spectrogram(s) ('echo'); 'sonar' = range x azimuth image from the ambisonic click response
        ('sonar', see compute_sonar; no binaural render). beams: active sensing -- a list of (name, yaw_deg, dipole_weight, dipole_power);
        the action becomes (navigation, beam): the click of this step is emitted with that beam (yaw + = left, dipole 0 = omnidirectional)
        and costs click_cost reward; the beam named 'none' emits nothing (zero observation, no cost). Integer actions use the first
        emitting beam. The observation after reset() uses that default beam."""
        """aux_directions: yaw offsets (deg, + = left) at which the distance to the nearest surface at head height is ray-cast each step
        and reported in info['aux_dist'] (training labels for an auxiliary loss; never part of the observation)."""
        """explore: no goal; reward = coverage_reward per newly visited coverage_cell x coverage_cell navmesh cell + slack - collision penalty;
        episodes run max_steps (STOP is a no-op). contact: observe 'contact' = 1 if the last action collided (a bump sensor)."""
        """scan_angles: head-scan echolocation. For each yaw offset (deg, + = left) the click is re-emitted with the head and a
        cardioid beam (click_dipole = (dipoleWeight, dipolePower)) turned by that angle, and the echoes are decoded binaurally at that head
        orientation; the echo observation stacks one (65, 64, 2) spectrogram per angle. None = single omnidirectional click at the body heading."""
        """goal_sound: the goal emits the clip (audio-goal observation 'spectrogram'); self_click: the agent emits a click each step and
        observes the binaural echo response ('echo'); pointgoal: observe the goal as (distance, bearing) in the listener frame ('pointgoal');
        sliding: Habitat wall sliding (False = a collision stops the agent, so obstacles must be detected and avoided)."""
        super().__init__()
        self.goal_sound, self.self_click, self.pointgoal, self.click_gain, self.collision_penalty = goal_sound, self_click, pointgoal, click_gain, collision_penalty
        self.scan_angles = None if scan_angles is None else [float(a) for a in scan_angles]; self.click_dipole = tuple(click_dipole)
        self.explore, self.contact, self.coverage_cell, self.coverage_reward = explore, contact, coverage_cell, coverage_reward
        self.aux_directions = None if aux_directions is None else [float(a) for a in aux_directions]; self.aux_max_range = aux_max_range
        self.echo_obs = echo_obs; self.beams = None if beams is None else [tuple(b) for b in beams]; self.click_cost = float(click_cost); self.sonar_bins = tuple(sonar_bins)
        self.default_beam = 0 if not self.beams else next((i for i, b in enumerate(self.beams) if b[0] != "none"), 0)
        self.current_beam = self.default_beam; self.n_clicks = 0
        self.echo_dropout = float(echo_dropout); self.drop_rng = np.random.RandomState(seed + 7919)   # training augmentation: blank echo observation with this probability
        self.rng = np.random.RandomState(seed); self.scene_glb = scene_glb
        self.step_size, self.turn_angle, self.success_distance, self.max_steps = step_size, turn_angle, success_distance, max_steps
        self.geodesic_range, self.agent_height = geodesic_range, agent_height
        self.slack_reward, self.success_reward = slack_reward, success_reward
        self.rays, self.bounces, self.ir_duration, self.order, self.air = rays, bounces, ir_duration, ambisonic_order, air_absorption
        self.want_rgb, self.want_depth = rgb, depth
        # ---------------- Habitat
        cfg = habitat_sim.SimulatorConfiguration(); cfg.scene_id = scene_glb; cfg.enable_physics = False; cfg.allow_sliding = sliding
        ac = habitat_sim.agent.AgentConfiguration(); ac.height = agent_height; ac.radius = 0.1
        specs = []
        if rgb:
            s = habitat_sim.CameraSensorSpec(); s.uuid = "rgb"; s.sensor_type = habitat_sim.SensorType.COLOR; s.resolution = [image_size, image_size]; s.position = [0, agent_height, 0]; specs.append(s)
        if depth:
            s = habitat_sim.CameraSensorSpec(); s.uuid = "depth"; s.sensor_type = habitat_sim.SensorType.DEPTH; s.resolution = [image_size, image_size]; s.position = [0, agent_height, 0]; specs.append(s)
        if not specs:   # habitat-sim wants at least one sensor
            s = habitat_sim.CameraSensorSpec(); s.uuid = "_dummy"; s.sensor_type = habitat_sim.SensorType.COLOR; s.resolution = [8, 8]; specs.append(s)
        ac.sensor_specifications = specs
        ac.action_space = {"move_forward": habitat_sim.agent.ActionSpec("move_forward", habitat_sim.agent.ActuationSpec(amount=step_size)),
                           "turn_left": habitat_sim.agent.ActionSpec("turn_left", habitat_sim.agent.ActuationSpec(amount=turn_angle)),
                           "turn_right": habitat_sim.agent.ActionSpec("turn_right", habitat_sim.agent.ActuationSpec(amount=turn_angle))}
        self.sim = habitat_sim.Simulator(habitat_sim.Configuration(cfg, [ac])); self.agent = self.sim.get_agent(0); self.pf = self.sim.pathfinder
        self.sim.seed(seed)
        # ---------------- Steam Audio
        V, T, self.mesh_frame = load_scene_mesh(scene_glb, self.pf)
        self.ray_mesh = None
        if self.aux_directions:
            import trimesh; self.ray_mesh = trimesh.Trimesh(V, T, process=False); self.ray_mesh.ray   # builds the rtree once
        self.ctx = sa.Context(lib_path=lib_path); self.scene = sa.Scene(self.ctx)
        name, absorption, scattering, transmission = material
        self.scene.add_mesh(V, T, [sa.Material.of(absorption, scattering, transmission)]); self.scene.commit()
        self.asim = sa.Simulator(self.ctx, self.scene, max_rays=rays, max_duration=ir_duration, max_order=ambisonic_order,
                                 sampling_rate=AUDIO_SR, frame_size=256, threads=threads, max_sources=2)
        self.src = self.asim.add_source() if goal_sound else None
        self.click_src = self.asim.add_source() if self_click else None
        self.asim.commit()
        self.renderer = sa.BinauralRenderer(self.ctx, ambisonic_order, AUDIO_SR, 256)
        self.n_tri = len(T)
        # ---------------- sounds (16 kHz, 1 s, SoundSpaces clips)
        self.sounds = {}
        for name in sounds:
            d, sr = sf.read(os.path.join(sounds_dir, name)); d = d.mean(axis=1) if d.ndim > 1 else d
            self.sounds[name] = librosa.resample(d.astype(np.float32), orig_sr=sr, target_sr=SS_SR)[:SS_SR]
        self.sound_names = list(self.sounds)
        # ---------------- spaces
        obs = {}
        if goal_sound: obs["spectrogram"] = spaces.Box(low=0, high=np.inf, shape=compute_spectrogram(np.ones((2, SS_SR), np.float32)).shape, dtype=np.float32)
        if self_click and echo_obs == "sonar":
            obs["sonar"] = spaces.Box(low=-np.inf, high=np.inf, shape=(self.sonar_bins[0], self.sonar_bins[1], 2), dtype=np.float32)
        elif self_click:
            e = compute_echo_spectrogram(np.ones((2, SS_SR), np.float32)).shape; n_scan = len(self.scan_angles) if self.scan_angles else 1
            obs["echo"] = spaces.Box(low=0, high=np.inf, shape=(e[0], e[1], e[2] * n_scan), dtype=np.float32)
        if pointgoal: obs["pointgoal"] = spaces.Box(low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32)
        if contact: obs["contact"] = spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
        if rgb: obs["rgb"] = spaces.Box(0, 255, (image_size, image_size, 3), np.uint8)
        if depth: obs["depth"] = spaces.Box(0, np.inf, (image_size, image_size, 1), np.float32)
        self.observation_space = spaces.Dict(obs); self.action_space = spaces.MultiDiscrete([4, len(self.beams)]) if self.beams else spaces.Discrete(4)
        self.episode = None; self.follower = None

    # ------------------------------------------------------------------ geometry helpers
    def geodesic(self, a, b):
        p = habitat_sim.ShortestPath(); p.requested_start = np.asarray(a, np.float32); p.requested_end = np.asarray(b, np.float32)
        return p.geodesic_distance if self.pf.find_path(p) else float("inf")

    def agent_pose(self):
        st = self.agent.get_state(); ahead, up = quat_to_ahead_up(st.rotation); return np.array(st.position, float), ahead, up

    def listener_position(self):
        p, _, _ = self.agent_pose(); return p + np.array([0, self.agent_height, 0])

    # ------------------------------------------------------------------ episodes
    def sample_episode(self, max_tries=200):
        lo, hi = self.geodesic_range
        for _ in range(max_tries):
            goal = np.array(self.pf.get_random_navigable_point(), float); start = np.array(self.pf.get_random_navigable_point(), float)
            g = self.geodesic(start, goal)
            if lo <= g <= hi and np.isfinite(g): return start, goal, g
        raise RuntimeError("could not sample an episode within the geodesic range")

    def reset(self, start=None, goal=None, sound=None, heading_deg=None):
        if start is None or goal is None: start, goal, g = self.sample_episode()
        else: start, goal = np.asarray(start, float), np.asarray(goal, float); g = self.geodesic(start, goal)
        st = self.agent.get_state(); st.position = start.astype(np.float32)
        yaw = self.rng.uniform(0, 2*np.pi) if heading_deg is None else np.radians(heading_deg)
        st.rotation = np.quaternion(math.cos(yaw/2), 0.0, math.sin(yaw/2), 0.0)
        self.agent.set_state(st)
        self.goal = goal; self.source_position = goal + np.array([0, self.agent_height, 0])
        self.sound = sound or self.sound_names[self.rng.randint(len(self.sound_names))]
        self.start_geodesic = g; self.prev_geodesic = g; self.n_steps = 0; self.path_length = 0.0; self.done = False; self.collisions = 0
        self.last_collided = False; self.visited = {self._cell(start)}; self.current_beam = self.default_beam; self.n_clicks = 0
        self.follower = habitat_sim.GreedyGeodesicFollower(self.pf, self.agent, goal_radius=self.success_distance,
                                                           forward_key="move_forward", left_key="turn_left", right_key="turn_right")
        self.episode = {"start": start, "goal": goal, "geodesic": g, "sound": self.sound, "scene": os.path.basename(self.scene_glb)}
        self.last_aux = self.aux_distances() if self.ray_mesh is not None else None
        return self._observe()

    # ------------------------------------------------------------------ acoustics
    def simulate_audio(self):
        """Steam Audio direct + reflections at the current pose for the goal source and/or the self-click source.
        Returns dict with 'goal': (ambisonic IR incl. direct path, binaural RIR 16 kHz, direct outputs) and/or 'echo': (ambisonic IR, binaural RIR)."""
        lis = self.listener_position(); _, ahead, up = self.agent_pose(); out = {}
        self.asim.set_listener(lis, ahead=ahead, up=up, num_rays=self.rays, bounces=self.bounces, duration=self.ir_duration, order=self.order,
                               irradiance_min=0.1 if self.self_click else 1.0)
        if self.src is not None: self.src.set_inputs(self.source_position, air_absorption=self.air)
        beam = self.beam_params()                        # None = no click this step
        if self.click_src is not None:
            if beam is None or self.echo_obs != "sonar": self.click_src.set_inputs(lis, air_absorption=self.air)
            else:
                yaw, w, pw = beam; self.click_src.set_inputs(lis, ahead=self.rotated(ahead, up, yaw), up=up, air_absorption=self.air, dipole_weight=w, dipole_power=pw)
        if self.src is None and self.click_src is not None and beam is None:
            out["echo"] = (None, None); return out       # nothing to simulate
        self.asim.run_direct(); self.asim.run_reflections()
        if self.src is not None:
            d = self.src.direct(); ir = self.asim.extract_ir(self.src, self.ir_duration, self.order)
            occ = d["occlusion"]; amp = d["distanceAttenuation"] * d["directivity"] * float(np.mean(d["airAbsorption"] * (occ + (1 - occ) * d["transmission"])))
            v = self.source_position - lis; dist = np.linalg.norm(v); u = v / max(dist, 1e-6)
            ir[0, 0] += amp
            if self.order >= 1:
                ir[1, 0] += -N3D * amp * u[0]; ir[2, 0] += N3D * amp * u[1]; ir[3, 0] += -N3D * amp * u[2]   # ACN/N3D, world frame
            binaural = self.renderer.render(ir, listener_ahead=ahead, listener_up=up)
            d["distance"] = dist; d["direct_amplitude"] = amp
            out["goal"] = (ir, resample_poly(binaural, SS_SR, AUDIO_SR, axis=1).astype(np.float32), d)
        if self.click_src is not None:
            # echoes only: the click's own direct sound (t = 0, constant) is left out; t = 0 is the emission instant
            if self.echo_obs == "sonar":
                out["echo"] = (None, None) if beam is None else (self.asim.extract_ir(self.click_src, self.ir_duration, self.order) * self.click_gain, None)
            elif not self.scan_angles:
                ir = self.asim.extract_ir(self.click_src, self.ir_duration, self.order) * self.click_gain
                binaural = self.renderer.render(ir, listener_ahead=ahead, listener_up=up)
                out["echo"] = (ir, resample_poly(binaural, SS_SR, AUDIO_SR, axis=1).astype(np.float32))
            else:
                irs, rirs = [], []
                for ang in self.scan_angles:
                    c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang)); right = np.cross(ahead, up)
                    a_rot = c * ahead - sn * right                       # + angle = head turned left
                    self.asim.set_listener(lis, ahead=a_rot, up=up, num_rays=self.rays, bounces=self.bounces, duration=self.ir_duration, order=self.order, irradiance_min=0.1)
                    self.click_src.set_inputs(lis, ahead=a_rot, up=up, air_absorption=self.air, dipole_weight=self.click_dipole[0], dipole_power=self.click_dipole[1])
                    self.asim.run_reflections()
                    ir = self.asim.extract_ir(self.click_src, self.ir_duration, self.order) * self.click_gain
                    binaural = self.renderer.render(ir, listener_ahead=a_rot, listener_up=up)
                    irs.append(ir); rirs.append(resample_poly(binaural, SS_SR, AUDIO_SR, axis=1).astype(np.float32))
                out["echo"] = (irs, rirs)
        return out

    def _observe(self):
        res = self.simulate_audio(); obs = {}
        if "goal" in res:
            ir, rir, d = res["goal"]; self.last_ir, self.last_rir, self.last_direct = ir, rir, d
            clip = self.sounds[self.sound]
            audio = np.stack([fftconvolve(clip, rir[0])[:SS_SR], fftconvolve(clip, rir[1])[:SS_SR]]); self.last_audio = audio
            obs["spectrogram"] = compute_spectrogram(audio)
        else:
            lis = self.listener_position(); self.last_direct = {"occlusion": float("nan"), "direct_amplitude": float("nan"), "distance": float(np.linalg.norm(self.source_position - lis))}
        if "echo" in res:
            self.last_echo_ir, self.last_echo_rir = res["echo"]
            if self.echo_obs == "sonar":
                _, ahead, up = self.agent_pose()
                obs["sonar"] = np.zeros((*self.sonar_bins, 2), np.float32) if self.last_echo_ir is None else compute_sonar(self.last_echo_ir, ahead, up, bins=self.sonar_bins)
            elif self.scan_angles: obs["echo"] = np.concatenate([compute_echo_spectrogram(r) for r in self.last_echo_rir], axis=-1)
            else: obs["echo"] = compute_echo_spectrogram(self.last_echo_rir)
        if self.echo_dropout > 0 and self.drop_rng.rand() < self.echo_dropout:
            for k in ("echo", "sonar"):
                if k in obs: obs[k] = np.zeros_like(obs[k])
        if self.pointgoal:
            az, el = self.source_bearing_deg(); obs["pointgoal"] = np.array([self.last_direct["distance"], math.radians(az)], np.float32)
        if self.contact: obs["contact"] = np.array([float(self.last_collided)], np.float32)
        if self.want_rgb or self.want_depth:
            o = self.sim.get_sensor_observations()
            if self.want_rgb: obs["rgb"] = o["rgb"][..., :3]
            if self.want_depth: obs["depth"] = o["depth"][..., None].astype(np.float32)
        return obs

    # ------------------------------------------------------------------ gym API
    def step(self, action):
        assert not self.done, "call reset()"
        action, self.current_beam = self.parse_action(action); beam = self.beam_params(); clicked = beam is not None and bool(self.beams)
        self.n_clicks += int(clicked); cost = self.click_cost if clicked else 0.0
        p0, _, _ = self.agent_pose(); self.n_steps += 1
        collided = False
        if self.explore and action == STOP: action = MOVE_FORWARD   # exploration has no stop
        if action != STOP:
            o = self.sim.step(ACTION_NAMES[int(action)]); collided = bool(o.get("collided", False)); self.collisions += int(collided)
        self.last_collided = collided
        p1, _, _ = self.agent_pose(); self.path_length += float(np.linalg.norm(p1 - p0))
        if self.explore:
            c = self._cell(p1); new_cell = c not in self.visited; self.visited.add(c)
            reward = self.slack_reward + (self.coverage_reward if new_cell else 0.0) - (self.collision_penalty if collided else 0.0) - cost
            success = False; self.done = self.n_steps >= self.max_steps; g = float("nan"); euclid = float("nan"); spl = 0.0
            obs = self._observe()
            info = {"aux_dist": self.aux_distances() if self.ray_mesh is not None else None, "step": self.n_steps, "collisions": self.collisions, "collided": collided, "coverage_cells": len(self.visited), "beam": self.current_beam, "clicks": self.n_clicks,
                    "coverage_m2": len(self.visited) * self.coverage_cell ** 2, "path_length": self.path_length, "success": False, "spl": 0.0,
                    "geodesic_distance": g, "distance_to_goal": euclid, "occlusion": self.last_direct["occlusion"], "direct_amplitude": self.last_direct["direct_amplitude"]}
            return obs, float(reward), self.done, info
        self.visited.add(self._cell(p1))
        g = self.geodesic(p1, self.goal); euclid = float(np.linalg.norm(p1 - self.goal))
        reward = self.slack_reward + (self.prev_geodesic - g) - (self.collision_penalty if collided else 0.0) - cost; self.prev_geodesic = g
        success = (action == STOP) and (g <= self.success_distance)
        if success: reward += self.success_reward
        self.done = (action == STOP) or (self.n_steps >= self.max_steps)
        obs = self._observe()
        spl = float(success) * self.start_geodesic / max(self.path_length, self.start_geodesic) if self.done else 0.0
        info = {"aux_dist": self.aux_distances() if self.ray_mesh is not None else None, "geodesic_distance": g, "distance_to_goal": euclid, "success": bool(success), "spl": spl, "step": self.n_steps,
                "occlusion": self.last_direct["occlusion"], "direct_amplitude": self.last_direct["direct_amplitude"], "collisions": self.collisions, "collided": collided,
                "coverage_cells": len(self.visited), "path_length": self.path_length, "beam": self.current_beam, "clicks": self.n_clicks}
        return obs, float(reward), self.done, info

    # ------------------------------------------------------------------ active sensing helpers
    def parse_action(self, action):
        """int -> (nav, default beam); (nav, beam) -> as given"""
        if self.beams and np.ndim(action) > 0: return int(action[0]), int(action[1])
        return int(action if np.ndim(action) == 0 else action[0]), self.default_beam

    def beam_params(self):
        """(yaw_deg, dipole_weight, dipole_power) of the current click, or None for no click. Without beams: an omnidirectional click."""
        if not self.beams: return (0.0, 0.0, 1.0)
        b = self.beams[self.current_beam]; return None if b[0] == "none" else (float(b[1]), float(b[2]), float(b[3]))

    @staticmethod
    def rotated(ahead, up, yaw_deg):
        """ahead vector turned by yaw_deg about up (+ = left)"""
        c, sn = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg)); return c * ahead - sn * np.cross(ahead, up)

    def _cell(self, p): return (int(np.floor(p[0] / self.coverage_cell)), int(np.floor(p[2] / self.coverage_cell)))

    def aux_distances(self):
        """distance (m, clipped to aux_max_range) to the nearest mesh surface along each aux direction at head height"""
        lis = self.listener_position(); _, ahead, up = self.agent_pose(); right = np.cross(ahead, up)
        dirs = np.array([math.cos(math.radians(a)) * ahead - math.sin(math.radians(a)) * right for a in self.aux_directions])
        locs, idx, _ = self.ray_mesh.ray.intersects_location(np.tile(lis, (len(dirs), 1)), dirs, multiple_hits=False)
        d = np.full(len(dirs), self.aux_max_range, np.float32)
        for l, i in zip(locs, idx): d[i] = min(d[i], float(np.linalg.norm(l - lis)))
        return d

    def oracle_action(self):
        """shortest-path follower action (SoundSpaces-style oracle)"""
        a = self.follower.next_action_along(self.goal.astype(np.float32))
        return {None: STOP, "stop": STOP, "move_forward": MOVE_FORWARD, "turn_left": TURN_LEFT, "turn_right": TURN_RIGHT}[a]

    def source_bearing_deg(self):
        """signed azimuth of the source in the listener frame (+ = left), and elevation"""
        lis = self.listener_position(); _, ahead, up = self.agent_pose(); right = np.cross(ahead, up)
        v = self.source_position - lis; v /= np.linalg.norm(v)
        return math.degrees(math.atan2(-np.dot(v, right), np.dot(v, ahead))), math.degrees(math.asin(np.clip(np.dot(v, up), -1, 1)))

    def close(self):
        try: self.renderer.release(); self.asim.release(); self.scene.release(); self.ctx.release()
        finally: self.sim.close()
