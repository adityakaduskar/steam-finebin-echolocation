"""Exercise SteamAudioNavEnv on a Habitat test scene: oracle and random episodes, acoustic cue sanity checks, timing."""
import os, sys, time, math, json
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
from habitat_audio import SteamAudioNavEnv, STOP
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import spearmanr

SCENE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/sound-spaces/data/versioned_data/habitat_test_scenes_1.0/apartment_1.glb")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"); os.makedirs(OUT, exist_ok=True)
lines, checks = [], []
def P(s=""): print(s, flush=True); lines.append(s)
def check(name, ok, detail): checks.append((name, bool(ok), detail)); P(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
EARLY = int(0.005 * 16000)   # 5 ms early window of the binaural RIR: direct sound + HRTF spread, before reflections dominate
def ild_db(rir, early=True):
    seg = rir[:, :EARLY] if early else rir
    return 10*np.log10((seg[0]**2).sum() / max((seg[1]**2).sum(), 1e-30))

t0 = time.time(); env = SteamAudioNavEnv(SCENE, rgb=True, image_size=64, seed=3); P(f"# {os.path.basename(SCENE)}: env created in {time.time()-t0:.1f} s; mesh frame {env.mesh_frame}, {env.n_tri} triangles, navmesh bounds {np.round(env.pf.get_bounds(), 2).tolist()}")
P(f"observation space: {env.observation_space}")

# ---------------------------------------------------------------- oracle episodes
P("\n## Oracle (shortest-path follower) episodes")
P("| episode | geodesic start [m] | steps | success | SPL | final distance [m] | occluded steps | steps/s |"); P("|---|---|---|---|---|---|---|---|")
traces = []; succ = []; spls = []; rates = []
for ep in range(5):
    obs = env.reset(); trace = []; t0 = time.time(); done = False; info = {}
    while not done:
        a = env.oracle_action(); obs, r, done, info = env.step(a)
        az, el = env.source_bearing_deg(); rir = env.last_rir; eL, eR = float((rir[0]**2).sum()), float((rir[1]**2).sum())
        pos = env.agent_pose()[0]
        trace.append(dict(step=info["step"], dist=info["distance_to_goal"], geo=info["geodesic_distance"], energy=eL+eR, ild=ild_db(rir), ild_full=ild_db(rir, False), az=az, occ=info["occlusion"], x=pos[0], z=pos[2], reward=r, action=int(a)))
    dt = time.time() - t0; rate = len(trace)/dt; rates.append(rate); succ.append(info["success"]); spls.append(info["spl"]); traces.append(({k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in env.episode.items()}, trace))
    P(f"| {ep} | {env.episode['geodesic']:.2f} | {len(trace)} | {info['success']} | {info['spl']:.2f} | {info['distance_to_goal']:.2f} | {sum(t['occ'] < 1 for t in trace)} | {rate:.1f} |")
check("oracle reaches the goal in every episode", all(succ), f"{sum(succ)}/5 successes, mean SPL {np.mean(spls):.2f}")
check("environment runs at >= 5 steps/s with audio (16384 rays, 12 bounces, 0.5 s IR)", np.mean(rates) >= 5, f"mean {np.mean(rates):.1f} steps/s")

# ---------------------------------------------------------------- acoustic cues
allt = [t for _, tr in traces for t in tr]
unocc = [t for t in allt if t["occ"] >= 1]
rho, _ = spearmanr([t["dist"] for t in unocc], [t["energy"] for t in unocc])
check("received energy decreases with distance (Spearman rho over unoccluded steps < -0.6)", rho < -0.6, f"rho = {rho:.2f} over {len(unocc)} steps")
lat = [t for t in allt if abs(t["az"]) > 25 and abs(t["az"]) < 155 and t["occ"] >= 1]
agree = np.mean([(t["ild"] > 0) == (t["az"] > 0) for t in lat]) if lat else float("nan")
agree_full = np.mean([(t["ild_full"] > 0) == (t["az"] > 0) for t in lat]) if lat else float("nan")
check("early-window (5 ms) interaural level difference sign matches the source side (|azimuth| 25-155 deg, unoccluded)", agree >= 0.85, f"{agree*100:.0f} % of {len(lat)} steps (whole-RIR energy ILD: {agree_full*100:.0f} %, diluted by reverberation)")
occ_steps = [t for t in allt if t["occ"] < 1]
if occ_steps and unocc:
    # compare energy at similar distances: occluded vs not (ratio of medians within 2-6 m)
    e_occ = np.median([t["energy"] for t in occ_steps if 2 < t["dist"] < 6] or [np.nan]); e_un = np.median([t["energy"] for t in unocc if 2 < t["dist"] < 6] or [np.nan])
    P(f"occluded steps: {len(occ_steps)}; median energy 2-6 m occluded / unoccluded = {e_occ/e_un:.2f}")
# turning in place: ILD must swing with heading while distance stays fixed
for _ in range(50):   # an unoccluded source within 4 m
    obs = env.reset(heading_deg=0.0)
    if env.last_direct["occlusion"] >= 1 and env.last_direct["distance"] < 4: break
ilds, ilds_full, azs = [], [], []
for k in range(36):
    obs, r, done, info = env.step(2)   # turn left 10 deg
    rir = env.last_rir; ilds.append(ild_db(rir)); ilds_full.append(ild_db(rir, False)); azs.append(env.source_bearing_deg()[0])
corr = np.corrcoef(np.sin(np.radians(azs)), ilds)[0, 1]; corr_full = np.corrcoef(np.sin(np.radians(azs)), ilds_full)[0, 1]
check("turning in place next to an unoccluded source: early ILD follows sin(azimuth) (correlation > 0.8)", corr > 0.8, f"corr = {corr:.2f}, early ILD range {min(ilds):.1f}..{max(ilds):.1f} dB (whole-RIR ILD corr {corr_full:.2f}, range {min(ilds_full):.1f}..{max(ilds_full):.1f} dB); source {env.last_direct['distance']:.1f} m")

# ---------------------------------------------------------------- random agent
P("\n## Random agent (5 episodes)")
rs = []; 
for ep in range(5):
    env.reset(); done = False; tot = 0
    while not done:
        a = env.action_space.sample()
        if a == STOP and env.n_steps < 20: a = 1
        _, r, done, info = env.step(a); tot += r
    rs.append((info["success"], tot, info["step"]))
P(f"successes {sum(s for s,_,_ in rs)}/5, mean return {np.mean([t for _,t,_ in rs]):.2f}, mean length {np.mean([n for _,_,n in rs]):.0f}")

# ---------------------------------------------------------------- figure
ep, tr = max(traces, key=lambda t: len(t[1]))
fig, axs = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
nv = np.array(env.pf.build_navmesh_vertices()); axs[0,0].scatter(nv[:,0], nv[:,2], s=2, c="lightgray")
axs[0,0].plot([t["x"] for t in tr], [t["z"] for t in tr], "b.-", ms=3, label="oracle path"); axs[0,0].plot(ep["goal"][0], ep["goal"][2], "r*", ms=14, label="sound source"); axs[0,0].plot(ep["start"][0], ep["start"][2], "gs", label="start")
axs[0,0].set_aspect("equal"); axs[0,0].set_xlabel("x [m]"); axs[0,0].set_ylabel("z [m]"); axs[0,0].legend(); axs[0,0].set_title("Longest oracle episode, top view (navmesh in gray)")
st = [t["step"] for t in tr]
axs[0,1].plot(st, [t["dist"] for t in tr], label="euclidean"); axs[0,1].plot(st, [t["geo"] for t in tr], label="geodesic"); axs[0,1].set_ylabel("distance to source [m]"); axs[0,1].legend(); axs[0,1].set_xlabel("step")
ax2 = axs[0,1].twinx(); ax2.plot(st, 10*np.log10([t["energy"] for t in tr]), "g", alpha=0.6); ax2.set_ylabel("received RIR energy [dB]", color="g")
axs[1,0].plot(st, [t["az"] for t in tr], label="source azimuth (+left) [deg]"); axs[1,0].plot(st, [t["ild"] for t in tr], label="early ILD (L-R, first 5 ms) [dB]"); axs[1,0].plot(st, [100*(t["occ"] < 1) for t in tr], "r:", label="occluded x100"); axs[1,0].legend(); axs[1,0].set_xlabel("step")
spec = obs["spectrogram"]; axs[1,1].imshow(spec[:, :, 0], origin="lower", aspect="auto"); axs[1,1].set_title(f"left-ear spectrogram {spec.shape} (log1p |STFT|, 16 kHz)"); axs[1,1].set_xlabel("time frame"); axs[1,1].set_ylabel("freq bin")
fig.savefig(os.path.join(OUT, "fig_audionav_episode.png"), dpi=120)

P("\n## Summary"); P(f"{sum(c[1] for c in checks)}/{len(checks)} checks passed")
open(os.path.join(OUT, "summary.md"), "w").write("\n".join(lines) + "\n"); json.dump(traces, open(os.path.join(OUT, "traces.json"), "w"), default=float)
env.close()
