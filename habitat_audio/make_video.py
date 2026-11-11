#!/usr/bin/env python3
"""Render episodes of a trained policy as video with sound.
Panels: first-person RGB (sensor attached at playback; policies never see it), top-down navmesh map with trajectory/source/heading,
the agent's own observation (binaural spectrogram and/or echo panels), HUD. Soundtrack: what the agent hears each step (goal clip through
the current room response, and/or click echoes), stitched continuously and muxed with ffmpeg.
python -m habitat_audio.make_video --ckpt runs/ppo_echo_scan_cp_1p5M/checkpoint.pt --episodes 2 --fps 4"""
import os, sys, math, argparse, subprocess, json
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
_EMB = os.path.expanduser("~/steamaudio/sdk/lib/patched_embree/libphonon.so")   # default to the Embree build when present (same physics, faster)
if os.path.exists(_EMB): os.environ.setdefault("STEAMAUDIO_LIB", _EMB); os.environ.setdefault("STEAMAUDIO_EMBREE", "1")
from habitat_audio import SteamAudioNavEnv, STOP
from habitat_audio.audio_nav_env import SS_SR
from habitat_audio.ppo_train import Policy, SCENE, SCENES, ENV_KW, to_tensor, load_policy, greedy
import numpy as np, torch, cv2, soundfile as sf
from scipy.signal import fftconvolve
from habitat.utils.visualizations import maps
import imageio_ffmpeg

ACTION_NAMES = {0: "STOP", 1: "FORWARD", 2: "LEFT", 3: "RIGHT"}

def heat(img2d, h, w, vmax=None):
    """2-D array (freq, time) -> colour image h x w, low frequencies at the bottom"""
    x = np.asarray(img2d, np.float32); vmax = vmax or max(float(x.max()), 1e-6)
    x = np.clip(x / vmax, 0, 1) ** 0.5; x = (255 * x[::-1]).astype(np.uint8)   # gamma 0.5 so faint later echoes stay visible
    return cv2.applyColorMap(cv2.resize(x, (w, h), interpolation=cv2.INTER_NEAREST), cv2.COLORMAP_MAGMA)

def put(img, text, y, x=8, scale=0.5, color=(255, 255, 255)):
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3, cv2.LINE_AA); cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)

class TopDown:
    def __init__(self, env, size=360):
        p = env.agent_pose()[0]; self.pf = env.pf
        self.base = maps.get_topdown_map(self.pf, height=float(p[1]), map_resolution=512)
        self.res = self.base.shape; self.size = size
    def grid(self, pos): return maps.to_grid(float(pos[2]), float(pos[0]), self.res, pathfinder=self.pf)   # (row, col)
    def render(self, env, path, goal, scan_angles=None):
        img = maps.colorize_topdown_map(self.base).copy()
        if len(path) > 1:
            pts = [self.grid(p) for p in path]
            for a, b in zip(pts[:-1], pts[1:]): cv2.line(img, (a[1], a[0]), (b[1], b[0]), (30, 90, 220), 2)
        if goal is not None:
            g = self.grid(goal); cv2.circle(img, (g[1], g[0]), 7, (220, 40, 40), -1); cv2.circle(img, (g[1], g[0]), 11, (220, 40, 40), 2)
        pos, ahead, up = env.agent_pose(); c = self.grid(pos); tip = self.grid(pos + 0.6 * ahead)
        if scan_angles:
            right = np.cross(ahead, up)
            for ang in scan_angles:
                d = math.cos(math.radians(ang)) * ahead - math.sin(math.radians(ang)) * right; t = self.grid(pos + 1.2 * d)
                cv2.line(img, (c[1], c[0]), (t[1], t[0]), (90, 200, 90), 1)
        cv2.line(img, (c[1], c[0]), (tip[1], tip[0]), (20, 160, 20), 3); cv2.circle(img, (c[1], c[0]), 5, (20, 160, 20), -1)
        h, w = img.shape[:2]; s = self.size / max(h, w); img = cv2.resize(img, (int(w * s), int(h * s)))
        canvas = np.full((self.size, self.size, 3), 255, np.uint8); y0 = (self.size - img.shape[0]) // 2; x0 = (self.size - img.shape[1]) // 2
        canvas[y0:y0 + img.shape[0], x0:x0 + img.shape[1]] = img; return canvas

def click_pulse(sr=SS_SR, width_ms=0.4):
    n = int(sr * 0.004); t = (np.arange(n) - n / 2) / sr; return (np.exp(-0.5 * (t / (width_ms / 1000)) ** 2)).astype(np.float32)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True); ap.add_argument("--episodes", type=int, default=2); ap.add_argument("--fps", type=int, default=4)
    ap.add_argument("--greedy", action="store_true"); ap.add_argument("--seed", type=int, default=777); ap.add_argument("--out", default=os.path.expanduser("~/steamaudio/habitat_audio/videos"))
    ap.add_argument("--image-size", type=int, default=360); ap.add_argument("--max-steps", type=int, default=None); ap.add_argument("--geodesic", type=float, nargs=2, default=None); ap.add_argument("--scene", default="apartment_1")
    args = ap.parse_args(); os.makedirs(args.out, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu"); ck = torch.load(args.ckpt, map_location=device)
    kw = dict(ck.get("env_kw", ENV_KW)); kw["threads"] = 8; kw["rgb"] = True; kw["image_size"] = args.image_size
    if args.geodesic: kw["geodesic_range"] = tuple(args.geodesic)
    if args.max_steps: kw["max_steps"] = args.max_steps
    kw.pop("aux_directions", None); kw.pop("echo_dropout", None); env = SteamAudioNavEnv(SCENES.get(args.scene, args.scene), seed=args.seed, **kw); policy, keys = load_policy(ck, device)
    name = os.path.basename(os.path.dirname(os.path.abspath(args.ckpt))); S = args.image_size; nseg = SS_SR // args.fps; pulse = click_pulse()
    scan = env.scan_angles; n_scan = len(scan) if scan else 1
    for ep in range(args.episodes):
        obs = env.reset(); top = TopDown(env, S); path = [env.agent_pose()[0].copy()]
        h = torch.zeros(1, 512, device=device); pa = torch.full((1,), 4, dtype=torch.long, device=device); nb = policy.n_beams
        pb = torch.full((1,), nb, dtype=torch.long, device=device) if nb else None
        frames, audio, done, info, step, a = [], [], False, {"step": 0, "collisions": 0}, 0, None
        goal = None if env.explore else env.goal
        while True:
            # ---- frame for the current state
            rgb = cv2.cvtColor(np.ascontiguousarray(obs["rgb"]), cv2.COLOR_RGB2BGR); td = top.render(env, path, goal, scan)
            panels = []
            if "spectrogram" in obs:
                sp = obs["spectrogram"]; panels.append(("goal sound, left ear (log|STFT|, 16 kHz)", heat(sp[:, :, 0], S // 2 - 12, S, vmax=float(sp.max()) or 1)))
                panels.append(("goal sound, right ear", heat(sp[:, :, 1], S // 2 - 12, S, vmax=float(sp.max()) or 1)))
            if "sonar" in obs:
                so = obs["sonar"][:, :, 0]; bname = env.beams[env.current_beam][0] if env.beams else "omni"
                panels.append((f"sonar image: range 0-11 m (up) x azimuth (ahead centre, left = right side)  click: {bname}", heat(so, S // 2 - 12, S, vmax=float(so.max()) or 1)))
            if "echo" in obs:
                e = obs["echo"]; vmax = float(e.max()) or 1; ph = (S // n_scan) - 12
                for i in range(n_scan):
                    lbl = f"echoes {'%+d deg' % scan[i] if scan else ''}: L | R  (0-128 ms)"
                    panels.append((lbl, np.concatenate([heat(e[:, :, 2*i], ph, S // 2, vmax), heat(e[:, :, 2*i+1], ph, S // 2, vmax)], 1)))
            right = np.zeros((S, S, 3), np.uint8); y = 0
            for lbl, im in panels[:max(1, len(panels))]:
                hh = min(im.shape[0], S - y - 12)
                if hh <= 0: break
                put(right, lbl, y + 10, scale=0.38); right[y + 12:y + 12 + hh, :im.shape[1]] = im[:hh]; y += hh + 12
            frame = np.concatenate([rgb, td, right], 1); bar = np.zeros((44, frame.shape[1], 3), np.uint8)
            if env.explore: txt = f"{name}  ep {ep}  step {step}  action {ACTION_NAMES.get(a[0] if isinstance(a, tuple) else a, '-')}  coverage {info.get('coverage_cells', len(env.visited))} cells  collisions {info.get('collisions', 0)}"
            else: txt = f"{name}  ep {ep}  step {step}  action {ACTION_NAMES.get(a[0] if isinstance(a, tuple) else a, '-')}  dist {env.last_direct['distance']:.2f} m  geodesic {info.get('geodesic_distance', env.prev_geodesic):.2f} m  collisions {info.get('collisions', 0)}" + ("  SUCCESS" if info.get("success") else "")
            put(bar, txt, 28, scale=0.5); frames.append(np.concatenate([frame, bar], 0))
            # ---- audio for this step (what the agent hears during 1/fps s)
            seg = np.zeros((2, nseg), np.float32)
            if "spectrogram" in obs:
                t0 = (step * nseg) % SS_SR; chunk = env.last_audio[:, t0:t0 + nseg]; seg[:, :chunk.shape[1]] += chunk
            if "echo" in obs:
                rirs = env.last_echo_rir if scan else [env.last_echo_rir]; sub = nseg // n_scan
                for i, r in enumerate(rirs):
                    eh = np.stack([fftconvolve(pulse, r[0][:int(0.128 * SS_SR)]), fftconvolve(pulse, r[1][:int(0.128 * SS_SR)])])[:, :sub]
                    seg[:, i * sub:i * sub + eh.shape[1]] += eh
            audio.append(seg)
            if done: break
            with torch.no_grad(): dist, v, h = policy.step(to_tensor([obs], device, keys), pa, h, torch.ones(1, device=device), pb)
            act = greedy(dist) if args.greedy else dist.sample()
            if nb: a = (int(act[0, 0]), int(act[0, 1])); pa = act[:, 0]; pb = act[:, 1]
            else: a = int(act.item()); pa = torch.tensor([a], device=device)
            obs, r, done, info = env.step(a); step += 1; path.append(env.agent_pose()[0].copy())
        # ---- encode
        A = np.concatenate(audio, 1); A = (A / max(np.abs(A).max(), 1e-9) * 0.9).astype(np.float32)
        base = os.path.join(args.out, f"{name}_ep{ep}"); sf.write(base + ".wav", A.T, SS_SR)
        H, W = frames[0].shape[:2]; ff = imageio_ffmpeg.get_ffmpeg_exe()
        p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(args.fps), "-i", "-",
                              "-i", base + ".wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-shortest", base + ".mp4"], stdin=subprocess.PIPE)
        for f in frames: p.stdin.write(np.ascontiguousarray(f).tobytes())
        p.stdin.close(); p.wait(); cv2.imwrite(base + "_frame.png", frames[min(len(frames) - 1, max(2, len(frames) // 2))])
        res = f"success {info.get('success')}" if not env.explore else f"coverage {info.get('coverage_cells')} cells"
        print(f"episode {ep}: {step} steps, {res}, collisions {info.get('collisions')}, {len(frames)/args.fps:.0f} s of video -> {base}.mp4", flush=True)
    env.close()

if __name__ == "__main__": main()
