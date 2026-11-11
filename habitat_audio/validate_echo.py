"""Echolocation observation check: the first echo must arrive at 2 x (distance to the nearest surface) / c."""
import os, sys, numpy as np, trimesh
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
from habitat_audio import SteamAudioNavEnv
from habitat_audio.scene_mesh import load_scene_mesh
SCENE = os.path.expanduser("~/sound-spaces/data/versioned_data/habitat_test_scenes_1.0/apartment_1.glb")
env = SteamAudioNavEnv(SCENE, goal_sound=False, self_click=True, pointgoal=True, sliding=False, rays=16384, bounces=4, ir_duration=0.3, threads=8, seed=5)
V, T, _ = load_scene_mesh(SCENE, env.pf); mesh = trimesh.Trimesh(V, T, process=False); pq = trimesh.proximity.ProximityQuery(mesh)
# HRTF decoder latency: render a t=0 impulse and find its binaural onset
from pysteamaudio import steamaudio as sa
from scipy.signal import resample_poly
imp = np.zeros((4, 4800)); imp[0, 0] = 1.0; st = resample_poly(env.renderer.render(imp), 16000, 24000, axis=1); e0 = st[0]**2 + st[1]**2
LAT = int(np.flatnonzero(e0 >= 0.02*e0.max())[0]) / 16000 * 1000; print(f"HRTF decoder latency (onset of a t=0 impulse): {LAT:.2f} ms")
print("| pose | nearest surface [m] | predicted first echo [ms] | measured first echo - latency [ms] | error [ms] | forward wall [m] | echo energy |"); print("|---|---|---|---|---|---|---|")
errs = []
for k in range(12):
    env.reset(); 
    for _ in range(k % 4): env.step(2)
    lis = env.listener_position(); _, ahead, _ = env.agent_pose(); d_near = float(pq.signed_distance([lis])[0]); d_near = abs(d_near)
    locs, idx, _ = mesh.ray.intersects_location([lis], [ahead], multiple_hits=False); d_fwd = float(np.linalg.norm(locs[0] - lis)) if len(idx) else float("nan")
    e = env.last_echo_rir[0]**2 + env.last_echo_rir[1]**2; on = int(np.flatnonzero(e >= 0.02*e.max())[0]) / 16000 * 1000 - LAT
    pred = 2*d_near/340*1000; errs.append(on - pred)
    print(f"| {k} | {d_near:.2f} | {pred:.1f} | {on:.1f} | {on-pred:+.1f} | {d_fwd:.2f} | {e.sum():.3e} |")
print(f"max |error| = {max(abs(x) for x in errs):.1f} ms (1 ms = 17 cm of range); echo obs shape {env.observation_space['echo'].shape}, pointgoal {env.observation_space['pointgoal'].shape}")
env.close()
