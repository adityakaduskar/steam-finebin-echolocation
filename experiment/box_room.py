#!/usr/bin/env python3
"""Shoebox room experiment with the Steam Audio Python binding.
Part 1: early reflections vs the image-source model (arrival samples, energies, directions, energy decay curve).
Part 2: reverberation time vs Eyring / Sabine, and Steam Audio's own parametric reverb estimate.
Usage: python3 box_room.py [--lib patched|stock] [--out results_box] [--rays N] [--quick]"""
import sys, os, math, json, time, argparse
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
from pysteamaudio import steamaudio as sa
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--lib", default="patched"); ap.add_argument("--out", default="results_box"); ap.add_argument("--rays", type=int, default=262144)
ap.add_argument("--quick", action="store_true"); args = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, args.out); os.makedirs(OUT, exist_ok=True)
LIB = os.path.expanduser(f"~/steamaudio/sdk/lib/{args.lib}/libphonon.so")
SPARSE = os.environ.get("STEAMAUDIO_RECONSTRUCTION") == "sparse" and args.lib.startswith("patched")
C_SA, SR, N_PHONG, HIT_OFFSET = 340.0, 48000, 100.0, 0.01

# room: x 0..6, y (up) 0..3, z 0..4 ; source and listener off-centre
SIZE = np.array([6.0, 3.0, 4.0]); SRC = np.array([1.7, 1.2, 1.1]); LIS = np.array([4.1, 1.6, 2.6])
V, T, F = sa.box_room(SIZE)
lines = []; checks = []
def P(s=""): print(s, flush=True); lines.append(s)
def check(name, ok, detail): checks.append((name, bool(ok), detail)); P(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")

def last_wall_cos(img):
    """cosine of the incidence angle at the last wall the unfolded path crosses before reaching the image (= the wall nearest the
    source along the physical path). Steam Audio shades the source contribution at that hit with a Blinn-Phong lobe whose
    energy scales with cos(theta) (measured: incidence_sweep.py), unlike a mirror."""
    d = img - LIS; r = np.linalg.norm(d); t_last, axis = -1.0, None
    for ax in range(3):
        lo, hi = sorted((LIS[ax], img[ax])); j0 = int(np.ceil(lo / SIZE[ax])); j1 = int(np.floor(hi / SIZE[ax]))
        for j in range(j0, j1 + 1):
            plane = j * SIZE[ax]
            if abs(plane - lo) < 1e-9 or abs(plane - hi) < 1e-9: continue
            t = (plane - LIS[ax]) / (img[ax] - LIS[ax])
            if t > t_last: t_last, axis = t, ax
    return 1.0 if axis is None else abs(d[axis]) / r

def image_sources(alpha, max_n=6):
    """shoebox image sources: list of (r, k, direction, energy_mirror, energy_steamaudio) with
    energy_mirror = (1-a)^k / r^2 and energy_steamaudio = energy_mirror * cos(theta at the last wall)"""
    out = []
    rng = range(-max_n, max_n + 1)
    for nx in rng:
        for px in (0, 1):
            for ny in rng:
                for py in (0, 1):
                    for nz in rng:
                        for pz in (0, 1):
                            img = np.array([2*nx*SIZE[0] + (-1)**px * SRC[0], 2*ny*SIZE[1] + (-1)**py * SRC[1], 2*nz*SIZE[2] + (-1)**pz * SRC[2]])
                            k = abs(2*nx - px) + abs(2*ny - py) + abs(2*nz - pz)
                            d = img - LIS; r = np.linalg.norm(d); em = (1 - alpha)**k / r**2
                            out.append((r, k, d / r, em, em * (last_wall_cos(img) if k > 0 else 1.0)))
    out.sort(key=lambda t: t[0]); return out

def run(alpha, scattering, bounces, duration, rays, reflection_type="convolution", order=1, air=False):
    ctx = sa.Context(lib_path=LIB); scene = sa.Scene(ctx)
    scene.add_mesh(V, T, [sa.Material.of(alpha, scattering)]); scene.commit()
    sim = sa.Simulator(ctx, scene, max_rays=rays, max_duration=duration, max_order=order, reflection_type=reflection_type, threads=16)
    src = sim.add_source(); sim.commit()
    sim.set_listener(LIS, num_rays=rays, bounces=bounces, duration=duration, order=order)
    src.set_inputs(SRC, air_absorption=air)
    t0 = time.time(); sim.run_direct(); sim.run_reflections(); dt = time.time() - t0
    direct = src.direct()
    if reflection_type == "convolution":
        ir = sim.extract_ir(src, duration, order); refl = None
    else:
        ir = None; refl = np.array(src.reflections().reverbTimes[:])
    sim.release(); scene.release(); ctx.release()
    return ir, direct, refl, dt

def schroeder(e):
    edc = np.cumsum(e[::-1])[::-1]; return 10*np.log10(np.maximum(edc / edc[0], 1e-30))

def rt60_from_edc(edc_db, sr, lo=-5, hi=-25):
    t = np.arange(edc_db.size) / sr; sel = (edc_db <= lo) & (edc_db >= hi)
    if sel.sum() < 10: return float("nan")
    m, b = np.polyfit(t[sel], edc_db[sel], 1); return -60.0 / m

V_room = float(np.prod(SIZE)); S_room = float(2*(SIZE[0]*SIZE[1] + SIZE[1]*SIZE[2] + SIZE[0]*SIZE[2])); mfp = 4*V_room/S_room
P(f"# Shoebox room {SIZE[0]} x {SIZE[2]} m floor, {SIZE[1]} m high (V = {V_room:.0f} m^3, S = {S_room:.0f} m^2, mean free path {mfp:.2f} m); source {SRC.tolist()}, listener {LIS.tolist()}")
P(f"library: {LIB}  mode: {'sparse (sample bins)' if SPARSE else 'stock linear (10 ms bins)'}  rays: {args.rays}\n")

# ----------------------------------------------------------------------------- Part 1: early reflections
alpha1 = 0.1
ir, direct, _, dt = run(alpha1, 0.0, bounces=3, duration=0.3, rays=args.rays)
W = ir[0]; e = W**2; r_direct = np.linalg.norm(SRC - LIS)
P(f"## Part 1: early reflections, alpha = {alpha1}, specular, 3 bounces ({dt:.1f} s simulation)")
P(f"direct path: distance {r_direct:.3f} m, distanceAttenuation {direct['distanceAttenuation']:.4f} (1/r = {1/r_direct:.4f}), occlusion {direct['occlusion']}")
imgs = image_sources(alpha1, max_n=3)
# first-order echoes (k=1), isolation test against all images up to k<=3 within 3 bounces
def arrival(im): return (im[0] - r_direct - im[1]*HIT_OFFSET)/C_SA*SR
def tau_of(r, cos_t=1.0): return (2*r/(N_PHONG+1))/C_SA*SR * (1 + cos_t*cos_t)/2   # mean length (samples) of the glossy-lobe tail; shorter at oblique incidence
imgs3 = [im for im in imgs if 1 <= im[1] <= 3]
groups = []
for im in sorted(imgs3, key=arrival):
    if groups and abs(arrival(im) - arrival(groups[-1][0])) < 0.5: groups[-1].append(im)
    else: groups.append([im])
P("\nFirst-order (single-wall) echoes. Predicted onset = floor((r - r_direct - k cm)/c * fs). Window = [onset-2, onset + 4 tau], tau = 2r/(n+1).")
P("The room is small, so other images (orders 1-3) overlap every window; the model energy for a window therefore sums every image whose")
P("exponential lobe tail falls inside it: E_model = sum_i E_i cos(theta_i) [exp(-max(0,lo-t_i)/tau_i) - exp(-(hi-t_i)/tau_i)], tau_i = 2 r_i/(n+1) (1+cos^2 theta_i)/2.")
P("'rise' = energy in the 4 samples from the predicted onset / energy in the 4 samples before it (an echo starts there if >> 1).")
P("| r [m] | onset | rise at onset | E window / model (cos theta) | E window / mirror model | model dir vector (energy-weighted mean of all images in window) | measured dir vector |")
P("|---|---|---|---|---|---|---|")
rise_ok, energy_ratio, dir_err = [], [], []
for g in groups:
    r, k = g[0][0], g[0][1]
    if k != 1: continue
    t_pred = arrival(g[0]); s0 = math.floor(t_pred); tau = tau_of(r, g[0][4]/g[0][3])
    lo, hi = max(s0 - 2, 0), int(s0 + 4*tau) + 2
    em = 0.0; es = 0.0; dvec = np.zeros(3)
    for im in imgs3:
        t_i = arrival(im); tau_i = tau_of(im[0], im[4]/im[3])
        if t_i > hi: continue
        frac = math.exp(-max(0.0, lo - t_i)/tau_i) - math.exp(-(hi - t_i)/tau_i)
        em += im[3]*frac; es += im[4]*frac; dvec += im[4]*frac*im[2]
    d = dvec/es; es *= (1 + 2/N_PHONG); em *= (1 + 2/N_PHONG)   # d = energy-weighted mean direction vector of everything in the window (|d| < 1 when directions mix)
    Ew = e[lo:hi+1].sum(); ratio = Ew/es
    before = e[max(s0-4, 0):s0].sum(); after = e[s0:s0+4].sum(); rise = after/max(before, 1e-30)
    near = [h for h in groups if h is not g and abs(arrival(h[0]) - t_pred) < 6]
    Wd = W[lo:hi+1]; ww = (Wd**2).sum(); md = np.array([-(ir[1][lo:hi+1]*Wd).sum(), (ir[2][lo:hi+1]*Wd).sum(), -(ir[3][lo:hi+1]*Wd).sum()])/ww/math.sqrt(3)
    if not near: rise_ok.append(rise > 3)
    energy_ratio.append(ratio); dir_err.append(float(np.abs(md - d).max()))
    P(f"| {r:.3f} | {s0} | {rise:.1f}{'' if not near else ' (another image within 6 samples)'} | {ratio:.3f} | {Ew/em:.3f} | ({d[0]:+.2f},{d[1]:+.2f},{d[2]:+.2f}) | ({md[0]:+.2f},{md[1]:+.2f},{md[2]:+.2f}) |")
if SPARSE:
    check("first-order echoes start at the image-source sample (energy rise > 3x at the predicted onset)", bool(rise_ok) and all(rise_ok), f"{sum(rise_ok)}/{len(rise_ok)} echoes with an unambiguous onset")
    check("energy in each first-order echo window matches the cos(theta) image-source model within 15 %", max(abs(x-1) for x in energy_ratio) < 0.15, f"ratios {[round(float(x),3) for x in energy_ratio]}")
    check("direction vector of each first-order echo window matches the model (|err| < 0.2; windows contain several overlapping images)", max(dir_err) < 0.2, f"max |err| {max(dir_err):.3f}")

# energy decay curve vs image-source model over the first 80 ms
n80 = int(0.045*SR); e_meas = e[:n80].copy()   # 3-bounce images exist up to ~45 ms in this room
e_model = np.zeros(n80); e_mirror = np.zeros(n80)
for r, k, d, em, es in imgs:
    if k == 0 or k > 3: continue
    t = (r - r_direct - k*HIT_OFFSET)/C_SA*SR
    if 0 <= t < n80: e_model[int(t)] += es * (1 + 2/N_PHONG); e_mirror[int(t)] += em * (1 + 2/N_PHONG)
edc_m, edc_p, edc_mirror = schroeder(e_meas), schroeder(e_model), schroeder(e_mirror)
P(f"\nEnergy decay curve 0-45 ms, 3-bounce image-source models vs simulation. Total early energy: sim / mirror model = {e_meas.sum()/e_mirror.sum():.3f}, sim / cos(theta) model = {e_meas.sum()/e_model.sum():.3f}")
P("| t [ms] | EDC mirror model [dB] | EDC cos(theta) model [dB] | EDC simulated [dB] |"); P("|---|---|---|---|")
dev = []
for ms in [5, 10, 15, 20, 25, 30, 35, 40]:
    i = int(ms/1000*SR); dev.append(abs(edc_m[i] - edc_p[i])); P(f"| {ms} | {edc_mirror[i]:.2f} | {edc_p[i]:.2f} | {edc_m[i]:.2f} |")
if SPARSE:
    check("energy decay curve matches the cos(theta) image-source model within 1.5 dB over 0-40 ms", max(dev) < 1.5, f"max deviation {max(dev):.2f} dB (mirror model: {max(abs(edc_m[int(ms/1000*SR)] - edc_mirror[int(ms/1000*SR)]) for ms in [5,10,15,20,25,30,35,40]):.2f} dB)")
    check("total early energy (0-45 ms, orders 1-3) matches the cos(theta) image-source model within 10 %", abs(e_meas.sum()/e_model.sum() - 1) < 0.10, f"ratio {e_meas.sum()/e_model.sum():.3f}; vs mirror model {e_meas.sum()/e_mirror.sum():.3f}")
fig, axs = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
t_ms = np.arange(n80)/SR*1000
axs[0].plot(t_ms, e_meas, lw=0.8, label="simulated energy per sample (W)")
for r, k, d, em, es in imgs:
    if 1 <= k <= 3:
        t = (r - r_direct - k*HIT_OFFSET)/C_SA*1000
        if t < 45: axs[0].vlines(t, 0, es*(1+2/N_PHONG)*0.25, color=["r", "orange", "g"][k-1], lw=1)
axs[0].set_xlabel("time after direct sound [ms]"); axs[0].set_ylabel("energy"); axs[0].set_title(f"Box room early reflections (alpha={alpha1}); stems = image sources (red k=1, orange k=2, green k=3)"); axs[0].legend(); axs[0].set_xlim(0, 45)
axs[1].plot(t_ms, edc_mirror, "k:", label="mirror image-source model"); axs[1].plot(t_ms, edc_p, "r--", label="image-source model with cos(theta) per reflection"); axs[1].plot(t_ms, edc_m, label="simulated"); axs[1].set_xlabel("time [ms]"); axs[1].set_ylabel("EDC [dB]"); axs[1].legend()
fig.savefig(os.path.join(OUT, "fig_box_early.png"), dpi=130); plt.close(fig)
np.save(os.path.join(OUT, "ir_early_alpha0.1.npy"), ir)

# ----------------------------------------------------------------------------- Part 2: reverberation
P("\n## Part 2: reverberation time (no air absorption)")
P("Eyring: T60 = 55.26 V / (c S (-ln(1-alpha))), Sabine: 55.26 V / (c S alpha), c = 340 m/s. Measured: Schroeder backward integration of the W channel, slope fit -5..-25 dB.")
P("| alpha | scattering | T60 Eyring [s] | Sabine [s] | measured T60 [s] | ratio meas/Eyring | Steam Audio parametric RT60 (3 bands) [s] | sim time [s] |")
P("|---|---|---|---|---|---|---|---|")
combos = [(0.1, 0.0), (0.1, 1.0), (0.3, 0.0), (0.3, 1.0), (0.5, 0.0), (0.5, 1.0)] if not args.quick else [(0.3, 0.0), (0.3, 1.0)]
ratios = {}; rows = []
for alpha, s in combos:
    T_ey = 55.26*V_room/(C_SA*S_room*(-math.log(1-alpha))); T_sab = 55.26*V_room/(C_SA*S_room*alpha)
    duration = min(3.0, max(1.0, 1.6*T_ey)); bounces = int(C_SA*duration/mfp) + 10
    rays = min(args.rays, 65536)
    ir2, _, _, dt = run(alpha, s, bounces=bounces, duration=duration, rays=rays)
    edc = schroeder(ir2[0]**2); T_meas = rt60_from_edc(edc, SR)
    _, _, rt_param, dt2 = run(alpha, s, bounces=bounces, duration=duration, rays=rays, reflection_type="parametric")
    ratios[(alpha, s)] = T_meas/T_ey; rows.append((alpha, s, T_ey, T_sab, T_meas, rt_param))
    P(f"| {alpha} | {s} | {T_ey:.3f} | {T_sab:.3f} | {T_meas:.3f} | {T_meas/T_ey:.3f} | {np.round(rt_param, 3).tolist()} | {dt:.1f} + {dt2:.1f} |")
    np.save(os.path.join(OUT, f"edc_alpha{alpha}_s{s}.npy"), edc[:int(duration*SR)])
diffuse = [v for (a, s), v in ratios.items() if s == 1.0]; spec = [v for (a, s), v in ratios.items() if s == 0.0]
check("diffuse walls (s=1): measured T60 within 15 % of Eyring", all(abs(v-1) < 0.15 for v in diffuse), f"ratios {[round(v,3) for v in diffuse]}")
P(f"specular walls (s=0): measured/Eyring ratios {[round(v,3) for v in spec]} (a specular shoebox is not a diffuse field; axial/tangential image families decay at their own rates)")
par_dev = [abs(rp.mean()/T_ey - 1) for (a, s, T_ey, T_sab, T_meas, rp) in rows if s == 1.0]
check("Steam Audio parametric RT60 estimate within 25 % of Eyring for diffuse walls", all(d < 0.25 for d in par_dev), f"relative deviations {[round(d,3) for d in par_dev]}")

fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
for alpha, s in combos:
    edc = np.load(os.path.join(OUT, f"edc_alpha{alpha}_s{s}.npy")); t = np.arange(edc.size)/SR
    ax.plot(t, edc, lw=1, label=f"alpha={alpha} s={s}")
    T_ey = 55.26*V_room/(C_SA*S_room*(-math.log(1-alpha))); ax.plot([0, T_ey], [0, -60], "k:", lw=0.8)
ax.set_ylim(-70, 2); ax.set_xlabel("time [s]"); ax.set_ylabel("Schroeder EDC [dB]"); ax.set_title("Box room energy decay; dotted = Eyring slope"); ax.legend(fontsize=8)
fig.savefig(os.path.join(OUT, "fig_box_edc.png"), dpi=130); plt.close(fig)

P("\n## Summary"); npass = sum(c[1] for c in checks); P(f"{npass}/{len(checks)} checks passed")
for n, ok, d in checks:
    if not ok: P(f"FAILED: {n} -- {d}")
open(os.path.join(OUT, "summary.md"), "w").write("\n".join(lines) + "\n")
json.dump([{"check": n, "pass": ok, "detail": d} for n, ok, d in checks], open(os.path.join(OUT, "checks.json"), "w"), indent=1)
