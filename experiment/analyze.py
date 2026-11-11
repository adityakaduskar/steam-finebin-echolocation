#!/usr/bin/env python3
"""Validate single-wall Steam Audio results against image-source acoustics.
Reads results/*.f32 + .json written by wall_experiment, prints a validation table, writes results/summary.md and PNG plots."""
import json, os, glob, math
import numpy as np
from scipy import signal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
import sys
MODE = "linear"; RES = os.path.join(HERE, "results")
_a = sys.argv[1:]
if "--mode" in _a: MODE = _a[_a.index("--mode")+1]
if "--results" in _a: RES = os.path.join(HERE, _a[_a.index("--results")+1])
SPARSE = (MODE == "sparse")
C_SA = 340.0          # Steam Audio's speed of sound (core/src/core/propagation_medium.h)
BIN = 0.010           # energy-field bin duration (energy_field.cpp: kBinDuration = 1e-2)
N_PHONG = 100.0       # specular lobe exponent (reflection_simulator.cpp: kSpecularExponent)
HIT_OFFSET = 0.01     # hit points are pushed 1 cm off the surface (reflection_simulator.cpp: kHitSurfaceOffset), shortening the hit-to-source leg

def load(name):
    m = json.load(open(os.path.join(RES, name + ".json")))
    ir = np.fromfile(os.path.join(RES, name + ".f32"), dtype=np.float32).reshape(m["numChannels"], m["numSamples"]).astype(np.float64)
    return ir, m

def bin_energy(w, sr):
    n = int(round(BIN * sr))
    nb = w.size // n
    return np.add.reduceat(w[:nb*n]**2, np.arange(0, nb*n, n))

def onset_bin(e, frac=0.02):
    if e.max() <= 1e-12: return None
    return int(np.flatnonzero(e > frac * e.max())[0])

def peak_sample(w, sr):
    e = np.convolve(w**2, np.ones(3)/3, mode="same")
    return int(np.argmax(e)) if e.max() > 1e-12 else -1

def onset_sample(w, sr, frac=0.1):
    """first sample whose energy exceeds frac x the cluster maximum"""
    e = w**2
    if e.max() <= 1e-12: return -1
    return int(np.flatnonzero(e >= frac * e.max())[0])

def centroid_samples(w, sr):
    e = w**2
    if e.sum() <= 1e-12: return float("nan")
    return float((np.arange(w.size) * e).sum() / e.sum())

def centroid_ms(w, sr):
    e = w**2
    if e.sum() <= 1e-12: return float("nan")
    t = np.arange(w.size) / sr
    return 1000.0 * (t * e).sum() / e.sum()

SOS = {
    "low":  signal.butter(4, 800, "lowpass", fs=48000, output="sos"),
    "mid":  signal.butter(4, [800, 8000], "bandpass", fs=48000, output="sos"),
    "high": signal.butter(4, 8000, "highpass", fs=48000, output="sos"),
}
def band_energies(w):
    return {k: float((signal.sosfilt(s, w)**2).sum()) for k, s in SOS.items()}


def field_energy(w, sr):
    """Undo the reconstructor's linear amplitude ramp: segment energy S_k = c (A_{k-1}^2 + A_{k-1}A_k + A_k^2)
    with c = (noise var 1/3)*(samples per bin)/3. Returns sum_k A_k^2 (proportional to energy-field energy)."""
    n = int(round(BIN*sr)); c = (1/3)*n/3
    S = bin_energy(w, sr); A_prev = 0.0; tot = 0.0
    for Sk in S:
        disc = 4*Sk/c - 3*A_prev**2
        A = 0.0 if disc <= 0 else (-A_prev + math.sqrt(disc))/2
        A = max(A, 0.0); tot += A*A; A_prev = A
    return tot

def rbj(kind, f1, f2=None, sr=48000):
    if kind == "lp":
        w0=2*np.pi*f1/sr; a=np.sin(w0)/(2*0.707); c=np.cos(w0); b=np.array([(1-c)/2,1-c,(1-c)/2])
    elif kind == "hp":
        w0=2*np.pi*f1/sr; a=np.sin(w0)/(2*0.707); c=np.cos(w0); b=np.array([(1+c)/2,-(1+c),(1+c)/2])
    else:
        fc=np.sqrt(f1*f2); qi=(f2-f1)/fc; w0=2*np.pi*fc/sr; a=np.sin(w0)*qi/2; c=np.cos(w0); b=np.array([a,0,-a])
    A=np.array([1+a,-2*c,1-a]); return b/A[0], A/A[0]
FREQ = np.linspace(0, np.pi, 48001)   # rad/sample, 0.5 Hz steps at 48 kHz
H_SA = [signal.freqz(*rbj("lp", 800), worN=FREQ)[1], signal.freqz(*rbj("bp", 800, 8000), worN=FREQ)[1], signal.freqz(*rbj("hp", 8000), worN=FREQ)[1]]
def _HB():
    # stock: forward IIR (complex response H_b, bands added coherently)
    # patched sparse: zero-phase complementary split: low = |H_lp|^2, high = |H_hp|^2, mid = 1 - low - high (sum = 1)
    if SPARSE:
        lo = np.abs(H_SA[0])**2; hi = np.abs(H_SA[2])**2
        return [lo, 1 - lo - hi, hi]
    return H_SA
def coherent_gain(a=(1,1,1)):
    """mean power of sum_b a_b H_b: all bands act on one shared impulse/noise sequence, so they add coherently"""
    H = _HB(); return float(np.mean(np.abs(a[0]*H[0] + a[1]*H[1] + a[2]*H[2])**2))
def spectral_ratio(w_case, w_ref, sr, f_lo, f_hi):
    N = 1 << 17
    P1 = np.abs(np.fft.rfft(w_case, N))**2; P0 = np.abs(np.fft.rfft(w_ref, N))**2
    f = np.fft.rfftfreq(N, 1/sr); sel = (f >= f_lo) & (f <= f_hi)
    return float(P1[sel].sum()/P0[sel].sum())
def pred_spectral_ratio(a, f_lo, f_hi, sr=48000):
    f = FREQ*sr/(2*np.pi); sel = (f >= f_lo) & (f <= f_hi)
    H = _HB(); num = np.abs(a[0]*H[0] + a[1]*H[1] + a[2]*H[2])**2; den = np.abs(H[0]+H[1]+H[2])**2
    return float(num[sel].sum()/den[sel].sum())

def refl_geometry(m):
    """image-source geometry for a plane wall perpendicular to axis at wallPos"""
    ax = "xyz".index(m["wallAxis"]); w = m["wallPos"]
    s = np.array(m["src"], float); l = np.array(m["lis"], float)
    img = s.copy(); img[ax] = 2*w - s[ax]
    r_dir = np.linalg.norm(s - l); r_ref = np.linalg.norm(img - l)
    d = (img - l) / r_ref
    return r_dir, r_ref, d, img

def direction_ratios(ir):
    W = ir[0]; ww = (W*W).sum()
    if ww <= 1e-12: return [float("nan")]*3
    return [float((ir[ch]*W).sum()/ww) for ch in (1, 2, 3)]

def pred_irradiance(m, r_ref, band=None):
    a = m["absorption"]; alpha = np.mean(a) if band is None else a[band]
    return (1 - alpha) * (1 + 2/N_PHONG) / (4*math.pi*r_ref**2)

lines = []
def P(s=""):
    print(s); lines.append(s)

checks = []   # (name, passed, detail)
def check(name, ok, detail):
    checks.append((name, bool(ok), detail)); P(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")

# ---------------------------------------------------------------- baseline IR picture
ir, m = load("B_abs_0.0"); sr = m["sr"]
W = ir[0]; e = bin_energy(W, sr)
P("# Steam Audio single-wall validation" + (" -- PATCHED core: sample-resolution bins + sparse reconstruction" if SPARSE else " -- stock libphonon 4.8.1") + "\n")
P(f"Baseline: source=listener at origin, wall x=+3 m (path 6 m), absorption 0, 65536 rays, order 1, {sr} Hz")
P(f"IR energy per 10 ms bin (W channel), first 5 bins: {np.array2string(e[:5], precision=3)}")
if SPARSE:
    P(f"onset sample = {onset_sample(W, sr)}, peak sample = {peak_sample(W, sr)}; image-source prediction 6 m / 340 m/s = {6/C_SA*sr:.2f} samples, minus the 1 cm hit-surface offset = {(6-HIT_OFFSET)/C_SA*sr:.2f} samples")
    P(f"energy centroid = {centroid_samples(W, sr):.2f} samples, i.e. {centroid_samples(W, sr)-(6-HIT_OFFSET)/C_SA*sr:.1f} samples after the arrival: the Phong lobe's exponential tail, predicted mean excess path 2w/(n+1) = {2*3/(N_PHONG+1)*100:.1f} cm = {2*3/(N_PHONG+1)/C_SA*sr:.1f} samples")
else:
    P(f"onset bin = {onset_bin(e)}  (predicted floor((6 m / 340 m/s)/10 ms) = {math.floor(6/C_SA/BIN)});  energy centroid = {centroid_ms(W, sr):.2f} ms")
fig, axs = plt.subplots(2, 1, figsize=(9, 6), constrained_layout=True)
t = np.arange(W.size)/sr*1000
if SPARSE:
    axs[0].plot(t[800:1000], W[800:1000], lw=1.0); axs[0].set_xlim(t[800], t[1000])
else:
    axs[0].plot(t[:2400], W[:2400], lw=0.6); axs[0].set_xlabel("time after direct arrival [ms]"); axs[0].set_ylabel("IR amplitude (W)")
axs[0].axvline(6/C_SA*1000, color="r", ls="--", label="image-source delay 17.65 ms"); axs[0].legend(); axs[0].set_title("Baseline IR: single wall at 3 m, co-located source/listener")
if SPARSE:
    axs[1].plot(np.arange(820, 920)/sr*1000, W[820:920]**2, lw=1.0); axs[1].set_xlabel("time after direct arrival [ms]"); axs[1].set_ylabel("energy per sample")
    axs[1].axvline(6/C_SA*1000, color="r", ls="--")
else:
    axs[1].bar(np.arange(10)*10+5, e[:10], width=9); axs[1].set_xlabel("10 ms bin [ms]"); axs[1].set_ylabel("energy per bin")
    axs[1].axvline(6/C_SA*1000, color="r", ls="--")
fig.savefig(os.path.join(RES, "fig1_baseline_ir.png"), dpi=130); plt.close(fig)

# ---------------------------------------------------------------- A: arrival time vs wall distance
P("\n## A. Reflection arrival time vs wall distance (listener origin, source 2 m ahead, wall x=w)")
rowsA = []
if SPARSE:
    P("| w [m] | path diff [m] | predicted delay [ms] | predicted onset sample (incl. 1 cm offset) | measured onset | error [samples] |")
    P("|---|---|---|---|---|---|")
else:
    P("| w [m] | path diff [m] | predicted delay [ms] | predicted bin | measured onset bin | centroid [ms] |")
    P("|---|---|---|---|---|---|")
for f in sorted(glob.glob(os.path.join(RES, "A_time_w*.json")), key=lambda p: float(p.split("_w")[-1][:-5])):
    name = os.path.basename(f)[:-5]; ir, m = load(name)
    r_dir, r_ref, d, _ = refl_geometry(m); dt = (r_ref - r_dir)/C_SA
    if SPARSE:
        ps = math.floor((r_ref - HIT_OFFSET - r_dir)/C_SA*sr); cs = onset_sample(ir[0], sr); rowsA.append((m["wallPos"], r_ref-r_dir, dt*1000, ps, cs, cs - ps))
        P(f"| {m['wallPos']} | {r_ref-r_dir:.3f} | {dt*1000:.3f} | {ps} | {cs} | {cs-ps:+d} |")
    else:
        e = bin_energy(ir[0], sr); ob = onset_bin(e); pb = math.floor(dt/BIN)
        rowsA.append((m["wallPos"], r_ref-r_dir, dt*1000, pb, ob, centroid_ms(ir[0], sr)))
        P(f"| {m['wallPos']} | {r_ref-r_dir:.3f} | {dt*1000:.2f} | {pb} | {ob} | {centroid_ms(ir[0], sr):.1f} |")
if SPARSE:
    errs = np.array([r[5] for r in rowsA]); pathd = np.array([r[1] for r in rowsA]) - HIT_OFFSET; cs_t = np.array([r[4] for r in rowsA])/sr
    check("reflection onset sample == floor((r_refl - 1 cm - r_direct)/c * sr) within 1 sample", np.abs(errs).max() <= 1, f"max |error| = {np.abs(errs).max():.0f} samples ({np.abs(errs).max()/sr*1e3:.3f} ms)")
    sl_t, ic_t = np.polyfit(pathd, cs_t, 1); c_est = 1/sl_t
    check("speed of sound from arrival-time fit = 340 m/s", abs(c_est - 340) < 1.0, f"fit over 13 distances: c = {c_est:.2f} m/s, intercept = {ic_t*1e6:.1f} us")
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    pred = np.array([r[2] for r in rowsA]); cent = np.array([r[4] for r in rowsA])/sr*1000
    ax.plot(pred, cent, "o", label="measured IR onset")
    ax.plot([0, pred.max()*1.05], [0, pred.max()*1.05], "r--", lw=1, label="ideal (image source, c=340 m/s)")
    ax.set_xlabel("predicted reflection delay after direct sound [ms]"); ax.set_ylabel("measured IR onset time [ms]"); ax.legend(); ax.set_title("A. Reflection arrival time (patched core)")
    fig.savefig(os.path.join(RES, "fig2_arrival_time.png"), dpi=130); plt.close(fig)
else:
    okA = all(r[3] == r[4] for r in rowsA)
    check("arrival bin == floor(((r_refl - r_direct)/340)/10ms) for all 13 wall distances", okA, f"{sum(r[3]==r[4] for r in rowsA)}/{len(rowsA)} match")
    cent = np.array([r[5] for r in rowsA]); pred = np.array([r[2] for r in rowsA]); sel = pred >= 10
    slope, icpt = np.polyfit(pred[sel], cent[sel], 1)
    check("linear fit centroid vs predicted delay (arrivals >= 10 ms): slope ~1 (c = 340 m/s)", abs(slope-1) < 0.05, f"slope={slope:.3f}, intercept={icpt:.1f} ms (expected ~+5..10 ms from 10 ms binning; bin-0 arrivals use a flat ramp and are excluded)")
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    ax.plot(pred, cent, "o", label="measured IR energy centroid")
    ax.step(np.linspace(0, pred.max()*1.05, 400), (np.floor(np.linspace(0, pred.max()*1.05, 400)/10)+1)*10, where="post", color="gray", lw=1, label="expected for 10 ms binning: (floor(t/10ms)+1)*10 ms")
    ax.plot([0, pred.max()*1.05], [0, pred.max()*1.05], "r--", lw=1, label="ideal (image source, c=340 m/s)")
    ax.set_xlabel("predicted reflection delay after direct sound [ms]"); ax.set_ylabel("measured IR centroid [ms]"); ax.legend(); ax.set_title("A. Reflection arrival time")
    fig.savefig(os.path.join(RES, "fig2_arrival_time.png"), dpi=130); plt.close(fig)

# ---------------------------------------------------------------- A2: IR time origin
P("\n## A2. IR time origin (wall x=3, source at distance d ahead)")
okA2 = True
if SPARSE:
    P("| d [m] | r_refl [m] | onset if origin=direct arrival | onset if origin=emission | measured onset |"); P("|---|---|---|---|---|")
else:
    P("| d [m] | r_refl [m] | bin if origin=direct arrival | bin if origin=emission | measured |"); P("|---|---|---|---|---|")
for f in sorted(glob.glob(os.path.join(RES, "A2_origin_d*.json")), key=lambda p: float(p.split("_d")[-1][:-5])):
    name = os.path.basename(f)[:-5]; ir, m = load(name)
    r_dir, r_ref, d, _ = refl_geometry(m)
    if SPARSE:
        s_rel = math.floor((r_ref-HIT_OFFSET-r_dir)/C_SA*sr); s_abs = math.floor((r_ref-HIT_OFFSET)/C_SA*sr); cs = onset_sample(ir[0], sr); okA2 &= abs(cs - s_rel) <= 2
        P(f"| {-m['src'][2]:g} | {r_ref:.3f} | {s_rel} | {s_abs} | {cs} |")
    else:
        b_rel = math.floor((r_ref-r_dir)/C_SA/BIN); b_abs = math.floor(r_ref/C_SA/BIN)
        ob = onset_bin(bin_energy(ir[0], sr)); okA2 &= (ob == b_rel)
        P(f"| {-m['src'][2]:g} | {r_ref:.3f} | {b_rel} | {b_abs} | {ob} |")
check("IR time zero is the direct-path arrival (reflection delay = (r_refl - r_direct)/c)", okA2, "all 5 source distances match the direct-relative prediction" + (" within 2 samples (42 us); the emission-time hypothesis is off by hundreds to thousands of samples" if SPARSE else ""))

# ---------------------------------------------------------------- A3: speed of sound
if SPARSE:
    P("\n## A3. Speed of sound (co-located, long paths): arrival sample vs path / c")
    P("| path [m] | predicted onset @340 m/s | @343 m/s | measured onset |"); P("|---|---|---|---|")
    errs340 = []
    for f in sorted(glob.glob(os.path.join(RES, "A3_sos_p*.json"))):
        name = os.path.basename(f)[:-5]; ir, m = load(name); path = 2*m["wallPos"]; cs = onset_sample(ir[0], sr)
        errs340.append(cs - (path-HIT_OFFSET)/340*sr); P(f"| {path} | {(path-HIT_OFFSET)/340*sr:.1f} | {(path-HIT_OFFSET)/343*sr:.1f} | {cs} |")
    P(f"At the default ray count the onset is off by up to {max(abs(e) for e in errs340):.1f} samples at 34-102 m: few listener rays land in each sample-wide annulus of the specular spot that far away.")
    P("Same geometry with 1048576 rays:"); P("| path [m] | predicted onset @340 m/s | @343 m/s | measured onset |"); P("|---|---|---|---|")
    errs_hi = []
    for f in sorted(glob.glob(os.path.join(RES, "A4_sos_hires_p*.json"))):
        name = os.path.basename(f)[:-5]; ir, m = load(name); path = 2*m["wallPos"]; cs = onset_sample(ir[0], sr)
        errs_hi.append(cs - (path-HIT_OFFSET)/340*sr); P(f"| {path} | {(path-HIT_OFFSET)/340*sr:.1f} | {(path-HIT_OFFSET)/343*sr:.1f} | {cs} |")
    check("speed of sound = 340 m/s (not 343) at 34-102 m paths (1M rays)", max(abs(e) for e in errs_hi) < 3.0, f"max |error| vs 340 m/s = {max(abs(e) for e in errs_hi):.2f} samples; 343 m/s would be off by 42-127 samples")
else:
    P("\n## A3. Speed of sound discrimination (co-located, path = 2w, bin index differs for c=340 vs c=343)")
    P("| path [m] | bin @340 m/s | bin @343 m/s | measured |")
    P("|---|---|---|---|")
    hits340 = hits343 = 0
    for f in sorted(glob.glob(os.path.join(RES, "A3_sos_p*.json"))):
        name = os.path.basename(f)[:-5]; ir, m = load(name); path = 2*m["wallPos"]
        b340 = math.floor(path/340/BIN); b343 = math.floor(path/343/BIN)
        ob = onset_bin(bin_energy(ir[0], sr)); hits340 += (ob == b340); hits343 += (ob == b343)
        P(f"| {path} | {b340} | {b343} | {ob} |")
    check("speed of sound = 340 m/s (not 343)", hits340 == 5 and hits343 < 5, f"340 m/s predicts {hits340}/5 bins, 343 m/s predicts {hits343}/5")

# ---------------------------------------------------------------- B: absorption
P("\n## B. Reflected energy vs wall absorption (co-located, wall 3 m)")
P("| alpha | E_W | E/E(0) | expected 1-alpha |")
P("|---|---|---|---|")
E0 = (load("B_abs_0.0")[0][0]**2).sum(); errB = []
for a in [0.0, 0.2, 0.4, 0.6, 0.8, 0.95]:
    ir, m = load(f"B_abs_{a}"); E = (ir[0]**2).sum(); errB.append(abs(E/E0 - (1-a)))
    P(f"| {a} | {E:.4e} | {E/E0:.4f} | {1-a:.2f} |")
check("E(alpha)/E(0) == 1 - alpha (energy absorption coefficient)", max(errB) < 0.01, f"max deviation {max(errB):.4f}")
P("\nPer-band absorption (alpha=0.9 in one band only). Measured: IR power-spectrum ratio to the alpha=0 run, averaged over a region inside each band.")
P("Predicted: |sum_b sqrt(1-alpha_b) H_b(f)|^2 / |sum_b H_b(f)|^2 with Steam Audio's 2nd-order RBJ band filters (LP 800 Hz, BP 800-8000 Hz, HP 8 kHz); all bands share one noise sequence so the sum is coherent.")
P("| case | region | measured | predicted |"); P("|---|---|---|---|")
W0 = load("B_abs_0.0")[0][0]; okBand = True; maxdev = 0
REG = {"low": (100, 400), "mid": (1500, 4000), "high": (12000, 20000)}
for case, b in [("B_abs_low", 0), ("B_abs_mid", 1), ("B_abs_high", 2)]:
    Wc, mc = load(case); a = np.sqrt(1 - np.array(mc["absorption"]))
    for reg, (lo, hi) in REG.items():
        meas = spectral_ratio(Wc[0], W0, sr, lo, hi); pred = pred_spectral_ratio(a, lo, hi)
        maxdev = max(maxdev, abs(meas - pred)); okBand &= abs(meas - pred) < 0.05
        P(f"| {case} | {reg} {lo}-{hi} Hz | {meas:.3f} | {pred:.3f} |")
check("absorption is applied per frequency band and matches the 2nd-order band-filter model", okBand, f"max |measured - predicted| spectral ratio = {maxdev:.3f}")

fig, ax = plt.subplots(figsize=(6, 4.5), constrained_layout=True)
al = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 0.95]); ax.plot(al, [ (load(f"B_abs_{a}")[0][0]**2).sum()/E0 for a in al], "o", label="measured E/E(0)")
ax.plot(al, 1-al, "r--", label="1 - alpha"); ax.set_xlabel("absorption coefficient alpha"); ax.set_ylabel("relative reflected energy"); ax.legend(); ax.set_title("B. Energy vs absorption")
fig.savefig(os.path.join(RES, "fig3_absorption.png"), dpi=130); plt.close(fig)

# ---------------------------------------------------------------- C: distance
P("\n## C. Reflected energy vs path length (co-located, path = 2w, air absorption disabled)")
P("| w [m] | r_refl [m] | E_W | E*r^2 | E / [(1+2/n)/(4 pi r^2)] |")
P("|---|---|---|---|---|")
rs, Es, Ks = [], [], []
AIR = np.array([0.0002, 0.0017, 0.0182])   # default air absorption coefficients (air_absorption.cpp)
for f in sorted(glob.glob(os.path.join(RES, "C3_noair_w*.json")), key=lambda p: float(p.split("_w")[-1][:-5])):
    name = os.path.basename(f)[:-5]; ir, m = load(name)
    r_dir, r_ref, d, _ = refl_geometry(m); E = (ir[0]**2).sum()
    bin0 = (not SPARSE) and (r_ref - r_dir)/C_SA < BIN
    if not bin0: rs.append(r_ref); Es.append(E); Ks.append(E / ((1+2/N_PHONG)/(4*math.pi*r_ref**2)))
    P(f"| {m['wallPos']} | {r_ref} | {E:.4e} | {E*r_ref**2:.4e} | {E / ((1+2/N_PHONG)/(4*math.pi*r_ref**2)):.3f} |" + (" (bin 0, excluded from fit)" if bin0 else ""))
sl, ic = np.polyfit(np.log(rs), np.log(Es), 1)
spread = np.std(np.array(Es)*np.array(rs)**2)/np.mean(np.array(Es)*np.array(rs)**2)
if SPARSE:
    P(f"\nCo-located sweep: log-log slope = {sl:.3f}, E*r^2 spread = {spread*100:.2f} % (no noise sequence in the patched reconstruction).")
    P("\nGlossy-lobe tail: the Phong lobe (n=100) spreads the reflection over an exponential tail of excess path. Weighting cos^(n+1)(theta)/r^4 over the wall gives a mean excess path of 2w/(n+1) for a=b=w.")
    P("| w [m] | arrival sample (2w - 1 cm)/c | energy centroid | centroid - arrival [samples] | predicted 2w/(n+1) -> samples | ratio |"); P("|---|---|---|---|---|---|")
    tail_ratio = []
    for f in sorted(glob.glob(os.path.join(RES, "C3_noair_w*.json")), key=lambda p: float(p.split("_w")[-1][:-5])):
        name = os.path.basename(f)[:-5]; ir, m = load(name); w = m["wallPos"]; W = ir[0]
        arr = (2*w - HIT_OFFSET)/C_SA*sr; cen = centroid_samples(W, sr); predt = (2*w/(N_PHONG+1))/C_SA*sr
        tail_ratio.append((cen - arr)/predt); P(f"| {w} | {arr:.1f} | {cen:.1f} | {cen-arr:.1f} | {predt:.1f} | {(cen-arr)/predt:.2f} |")
    check("Phong-lobe tail length (centroid - arrival) matches 2w/(n+1) within 15 %", max(abs(x-1) for x in tail_ratio) < 0.15, f"ratio range {min(tail_ratio):.2f}..{max(tail_ratio):.2f}")
else:
    P(f"\nCo-located sweep: log-log slope = {sl:.3f}, E*r^2 spread = {spread*100:.1f} %. Each distance lands in a different 10 ms bin, and the IR uses one fixed")
    P(f"noise sequence, so each bin has its own noise gain (+-10 %). r=4 m and r=6 m share bin 1 and agree to {abs(Es[0]/Es[1]*rs[0]**2/rs[1]**2-1)*100:.1f} %.")
    E15 = (load("C3_noair_w1.5")[0][0]**2).sum()*9; Eref = np.mean(np.array(Es[:2])*np.array(rs[:2])**2)
    check("stock quirk: an arrival inside the first 10 ms bin is rendered at ~2x energy (bin 0 uses a flat ramp instead of a ramp-up)", 1.7 < E15/Eref < 2.3, f"E*r^2 at 8.8 ms (bin 0) / E*r^2 in bin 1 = {E15/Eref:.2f}")
P("\nSame-bin sweep (wall x=3, listener origin, source on the wall normal at xs<=0: delay is always 2a/c = 17.6 ms, r_refl = 6 - xs), no air.")
P("(xs=+1.5 puts the source between listener and wall: delay 8.8 ms, bin 0, so it is listed but excluded from the same-bin fit)")
P("| xs [m] | r_refl [m] | E_W | E*r^2 |"); P("|---|---|---|---|")
rs4, Es4 = [], []
for f in sorted(glob.glob(os.path.join(RES, "C4_samebin_xs*.json")), key=lambda p: -float(p.split("_xs")[-1][:-5])):
    name = os.path.basename(f)[:-5]; ir, m = load(name); r_dir, r_ref, d, _ = refl_geometry(m); E = (ir[0]**2).sum()
    P(f"| {m['src'][0]} | {r_ref} | {E:.4e} | {E*r_ref**2:.4e} |")
    if m["src"][0] <= 0: rs4.append(r_ref); Es4.append(E)
sl4, _ = np.polyfit(np.log(rs4), np.log(Es4), 1); spread4 = np.std(np.array(Es4)*np.array(rs4)**2)/np.mean(np.array(Es4)*np.array(rs4)**2)
check("E proportional to 1/r_refl^2 (same-bin sweep, r = 6..103 m)", abs(sl4 + 2) < 0.02 and spread4 < 0.02, f"log-log slope = {sl4:.4f}; E*r^2 spread = {spread4*100:.2f} %")
check("E proportional to 1/r_refl^2 (co-located sweep, r = 3..80 m)", abs(sl + 2) < (0.02 if SPARSE else 0.1) and spread < (0.03 if SPARSE else 0.2), f"slope = {sl:.3f}; E*r^2 spread = {spread*100:.1f} %")
K_abs = float(np.median(Ks))
if SPARSE:
    K_pred = 4*math.pi*coherent_gain()
    check("absolute IR level: mirror reflection energy = 1/r_refl^2 (same scale as the direct effect) x filter gain", abs(K_abs/K_pred - 1) < 0.1,
          f"measured E_W / [(1+2/n)/(4 pi r^2)] = {K_abs:.3f}; predicted 4 pi x zero-phase filter-bank gain {coherent_gain():.3f} = {K_pred:.3f}")
else:
    K_pred = (1/3)*(320)/(4*math.pi)*coherent_gain()
    check("absolute IR level matches the analytic reconstruction model", abs(K_abs/K_pred - 1) < 0.1,
          f"measured E_W / [(1+2/n)/(4 pi r^2)] = {K_abs:.2f}; predicted (noise var 1/3) x (320 ramp samples) / (4 pi) x coherent filter gain {coherent_gain():.3f} = {K_pred:.2f}")
if SPARSE:
    P("\nAir absorption inside the IR (default model, k = 0.0002/0.0017/0.0182 per m, applied per sample at distance c*t). Measured as the power-spectrum ratio")
    P("of the default-air IR to the no-air IR inside each band region; predicted |sum_b exp(-k_b d/2) w_b(f)|^2 with the complementary band weights, i.e. ~exp(-k_b d) per band.")
    P("| w [m] | d = 2w [m] | low 100-400 Hz meas / pred | mid 1.5-4 kHz meas / pred | high 12-20 kHz meas / pred |"); P("|---|---|---|---|---|")
    okAir = True; maxdevAir = 0
    for w in [1.5, 2, 3, 4, 6, 8, 12, 16, 25, 40]:
        Wa = load(f"C_dist_w{w}")[0][0]; Wn = load(f"C3_noair_w{w}")[0][0]; d = 2*w; amp = np.exp(-AIR*0.5*d); cells = []
        for reg, (lo, hi) in REG.items():
            meas = spectral_ratio(Wa, Wn, sr, lo, hi); pred = pred_spectral_ratio(amp, lo, hi)
            maxdevAir = max(maxdevAir, abs(meas - pred)); okAir &= abs(meas - pred) < 0.05; cells.append(f"{meas:.3f} / {pred:.3f}")
        P(f"| {w} | {d} | " + " | ".join(cells) + " |")
    check("air absorption in reflections = exp(-k d) per band at the sample's distance", okAir, f"max |measured - predicted| spectral ratio = {maxdevAir:.3f}")
else:
    P("\nAir absorption inside the IR (default model, k = 0.0002/0.0017/0.0182 per m, applied per 10 ms bin at distance c*t_bin):")
    P("| w [m] | r_refl [m] | E(default air)/E(no air) measured | predicted |"); P("|---|---|---|---|")
    okAir = True; maxdevAir = 0
    for w in [1.5, 2, 3, 4, 6, 8, 12, 16, 25, 40]:
        Ea = (load(f"C_dist_w{w}")[0][0]**2).sum(); En = (load(f"C3_noair_w{w}")[0][0]**2).sum()
        ob = math.floor(2*w/C_SA/BIN)
        pred = 0.5*sum(coherent_gain(np.exp(-AIR*0.5*C_SA*(k+0.5)*BIN)) for k in (ob, ob+1))/coherent_gain()
        if ob == 0: pred *= 1.0  # bin 0 has a flat ramp; ratio unaffected
        maxdevAir = max(maxdevAir, abs(Ea/En - pred)); okAir &= abs(Ea/En - pred) < 0.03
        P(f"| {w} | {2*w} | {Ea/En:.4f} | {pred:.4f} |")
    check("air absorption in reflections = exp(-k d) per band at the bin distance", okAir, f"max |measured - predicted| = {maxdevAir:.4f}")

# C2: decouple listener-wall and source-wall distances
P("\n## C2. Listener-wall vs source-wall distance (wall x=3, listener origin, source on the wall normal at x=xs)")
P("| xs [m] | source-wall b [m] | listener-wall a [m] | r_refl=a+b | E_W | E*(a+b)^2 | E*b^2 |")
P("|---|---|---|---|---|---|---|")
vals = []
for f in sorted(glob.glob(os.path.join(RES, "C2_split_xs*.json")), key=lambda p: float(p.split("_xs")[-1][:-5])):
    name = os.path.basename(f)[:-5]; ir, m = load(name); r_dir, r_ref, d, _ = refl_geometry(m)
    xs = m["src"][0]; b = 3 - xs; a = 3.0; E = (ir[0]**2).sum()
    bin0 = (not SPARSE) and (r_ref - r_dir)/C_SA < BIN
    if not bin0: vals.append((a+b, b, E))
    P(f"| {xs} | {b} | {a} | {a+b} | {E:.4e} | {E*(a+b)**2:.4e} | {E*b*b:.4e} |" + (" (bin 0, excluded)" if bin0 else ""))
v = np.array(vals); cv_ab = np.std(v[:,2]*v[:,0]**2)/np.mean(v[:,2]*v[:,0]**2); cv_b = np.std(v[:,2]*v[:,1]**2)/np.mean(v[:,2]*v[:,1]**2)
check("energy follows image-source distance (a+b), not source-wall distance b", cv_ab < 0.15 and cv_b > 0.3, f"spread of E*(a+b)^2 = {cv_ab*100:.1f} %, spread of E*b^2 = {cv_b*100:.1f} %")

fig, ax = plt.subplots(figsize=(6.5, 4.5), constrained_layout=True)
ax.loglog(rs, Es, "o", label="co-located sweep (no air absorption)")
rr = np.array([min(rs), max(rs)]); ax.loglog(rr, K_abs*(1+2/N_PHONG)/(4*np.pi*rr**2), "r--", label="K (1+2/n) / (4 pi r^2)")
ax.loglog(rs4, Es4, "s", label="same-bin sweep (source moved along wall normal)")
ax.set_xlabel("image-source path length r_refl [m]"); ax.set_ylabel("IR energy (W channel)"); ax.legend(); ax.set_title("C. Reflected energy vs path length")
fig.savefig(os.path.join(RES, "fig4_distance.png"), dpi=130); plt.close(fig)

# ---------------------------------------------------------------- D: direction
P("\n## D. Reflection direction (first-order Ambisonics, ACN order, N3D). Ratio <ch*W>/<W*W>; expected sqrt(3) * (Y=-x, Z=+y, X=-z) component of image direction")
P("| case | image dir (x,y,z) | expected (Y,Z,X) | measured ch1,ch2,ch3 |")
P("|---|---|---|---|")
okD = True; maxerrD = 0
for name in ["D_dir_x3", "D_dir_x-3", "D_dir_y3", "D_dir_y-3", "D_dir_z3", "D_dir_z-3", "D_dir_diag"]:
    ir, m = load(name); r_dir, r_ref, d, _ = refl_geometry(m)
    exp = math.sqrt(3) * np.array([-d[0], d[1], -d[2]]); meas = np.array(direction_ratios(ir))
    err = np.abs(meas - exp).max(); maxerrD = max(maxerrD, err); okD &= err < 0.1
    P(f"| {name} | ({d[0]:+.2f},{d[1]:+.2f},{d[2]:+.2f}) | ({exp[0]:+.3f},{exp[1]:+.3f},{exp[2]:+.3f}) | ({meas[0]:+.3f},{meas[1]:+.3f},{meas[2]:+.3f}) |")
check("reflection arrives from the image-source direction (ambisonic Y/Z/X channels)", okD, f"max |error| = {maxerrD:.3f} (N3D gain sqrt(3)=1.732)")

# ---------------------------------------------------------------- E: scattering
P("\n## E. Scattering coefficient (co-located, wall 3 m, no air absorption)")
P("Analytic: infinite Lambertian wall lit by a point source at height h gives irradiance 1/(8 pi h^2) at the source position;")
P("specular (Phong n=100) gives (1+2/n)/(4 pi (2h)^2), ratio 1.961, so E(s)/E(0) = 1 + 0.961 s in the energy-field domain.")
P("Raw IR energy over-weights time-spread energy by up to 1.5x (linear amplitude ramps), so energies are first deconvolved back to per-bin energy-field values." if not SPARSE else "In the patched sparse mode the IR energy equals the energy-field energy directly, so the raw ratio is the test.")
P("| s | raw IR E/E(0) | deconvolved E/E(0) | expected 1+0.961 s | energy centroid [ms] | energy after 40 ms [%] |")
P("|---|---|---|---|---|---|")
E0raw = (load("E2_scat_noair_0.0")[0][0]**2).sum(); E0f = field_energy(load("E2_scat_noair_0.0")[0][0], sr); errE = []
for sc in [0.0, 0.5, 1.0]:
    ir, m = load(f"E2_scat_noair_{sc}"); W = ir[0]; e = bin_energy(W, sr)
    raw = (W**2).sum()/E0raw; dec = field_energy(W, sr)/E0f; exp_ = 1 + 0.961*sc; errE.append(abs(dec - exp_))
    P(f"| {sc} | {raw:.3f} | {dec:.3f} | {exp_:.3f} | {centroid_ms(W, sr):.1f} | {100*e[4:].sum()/e.sum():.1f} |")
if SPARSE:
    check("infinite diffuse wall: raw IR energy ratio E(s)/E(0) = 1 + 0.961 s (no reconstruction artefacts)", max(abs((load(f"E2_scat_noair_{sc}")[0][0]**2).sum()/E0raw - (1+0.961*sc)) for sc in [0.5, 1.0]) < 0.1,
          "raw ratios " + ", ".join(f"{(load(f'E2_scat_noair_{sc}')[0][0]**2).sum()/E0raw:.3f}" for sc in [0.5, 1.0]) + " vs 1.480, 1.961")
else:
    P("(deconvolution is only approximate because each bin carries a different noise gain; used here qualitatively)")
P("\nExact test: 2 m x 2 m panel at 3 m, co-located source/listener, no air. All reflected paths (6.0-6.6 m) fall in one 10 ms bin, so IR energy ratios are exact.")
from scipy import integrate
h = 3.0
Ediff_panel = (h*h/(4*math.pi**2)) * integrate.dblquad(lambda y, x: 1.0/(h*h + x*x + y*y)**3, -1, 1, -1, 1)[0]
Espec = (1 + 2/N_PHONG)/(4*math.pi*(2*h)**2)
R = Ediff_panel/Espec
P(f"Analytic: Lambertian panel irradiance = h^2/(4 pi^2) * integral dA / r^6 = {Ediff_panel:.4e}; specular = {Espec:.4e}; ratio R = {R:.4f}; expected E(s)/E(0) = 1 + s (R - 1)")
P("| s | measured E/E(0) | expected |"); P("|---|---|---|")
E0p = (load("E3_panel_scat_0.0")[0][0]**2).sum(); errP = []
for sc in [0.0, 0.25, 0.5, 0.75, 1.0]:
    E = (load(f"E3_panel_scat_{sc}")[0][0]**2).sum(); exp_ = 1 + sc*(R-1); errP.append(abs(E/E0p - exp_))
    P(f"| {sc} | {E/E0p:.4f} | {exp_:.4f} |")
check("scattering blends specular (Phong) and Lambertian diffuse reflection linearly: E(s)/E(0) = 1 + s (R - 1)", max(errP) < 0.02, f"max deviation {max(errP):.4f}")

# ---------------------------------------------------------------- F/G/H/I: geometry, occlusion, sidedness, empty
P("\n## F-I. Geometry, occlusion, transmission, sidedness")
Eon = (load("F_finite_on")[0][0]**2).sum(); Eoff = (load("F_finite_off")[0][0]**2).sum(); Eoffd = (load("F_finite_off_diffuse")[0][0]**2).sum(); Einf = (load("C_dist_w3")[0][0]**2).sum()
check("2x2 m panel: specular point on panel -> same energy as infinite wall", abs(Eon/Einf - 1) < 0.05, f"E_panel/E_infinite = {Eon/Einf:.3f}")
check("2x2 m panel: specular point 5 m off the panel -> no specular reflection", Eoff < 1e-6*Eon, f"E_off/E_on = {Eoff/Eon:.2e}")
check("same off-axis panel with scattering=1 -> diffuse reflection present", Eoffd > 1e-3*Eon, f"E_off_diffuse/E_on = {Eoffd/Eon:.3e}")
_, mo = load("G_occluded"); _, mu = load("G_unoccluded"); _, mf = load("G_unoccluded_far"); _, mn = load("G_near")
check("direct occlusion: wall between source and listener -> occlusion 0, transmission = material", mo["direct"]["occlusion"] == 0 and np.allclose(mo["direct"]["transmission"], [0.5, 0.3, 0.1]), f"occlusion={mo['direct']['occlusion']}, transmission={mo['direct']['transmission']}")
check("direct occlusion: clear line of sight -> occlusion 1, transmission 1", mu["direct"]["occlusion"] == 1 and np.allclose(mu["direct"]["transmission"], [1, 1, 1]), f"occlusion={mu['direct']['occlusion']}")
check("direct distance attenuation = 1/max(r, 1 m)", abs(mu["direct"]["distanceAttenuation"] - 1/6) < 1e-4 and abs(mf["direct"]["distanceAttenuation"] - 0.01) < 1e-4 and mn["direct"]["distanceAttenuation"] == 1.0, f"r=6: {mu['direct']['distanceAttenuation']:.4f}, r=100: {mf['direct']['distanceAttenuation']:.4f}, r=0.5: {mn['direct']['distanceAttenuation']:.3f}")
aa_pred = np.exp(-AIR*100); check("direct air absorption = exp(-k r), k = (0.0002, 0.0017, 0.0182) /m", np.allclose(mf["direct"]["airAbsorption"], aa_pred, atol=1e-3), f"r=100 m: measured {np.round(mf['direct']['airAbsorption'],4)}, expected {np.round(aa_pred,4)}")
Eocc = (load("G_occluded")[0][0]**2).sum()
check("source behind the wall -> no reflection energy", Eocc < 1e-6*Einf, f"E/E_baseline = {Eocc/Einf:.2e}")
Eflip = (load("H_flipped")[0][0]**2).sum()
check("wall triangles are two-sided (flipped winding gives same reflection)", abs(Eflip/Einf - 1) < 0.05, f"E_flipped/E = {Eflip/Einf:.3f}")
Enw = (load("I_nowall")[0][0]**2).sum()
check("empty scene -> IR is zero", Enw < 1e-9, f"E = {Enw:.2e}")

# ---------------------------------------------------------------- J: convergence
P("\n## J. Ray-count convergence (co-located, wall 3 m)")
P("| rays | E_W | E/E(262144) |")
P("|---|---|---|")
Eref = (load("J_rays_262144")[0][0]**2).sum(); devs = []
for n in [1024, 4096, 16384, 65536, 262144]:
    E = (load(f"J_rays_{n}")[0][0]**2).sum(); devs.append(abs(E/Eref-1)); P(f"| {n} | {E:.4e} | {E/Eref:.4f} |")
check("Monte Carlo estimate converged at 65536 rays", devs[3] < 0.02, f"|E(65536)/E(262144) - 1| = {devs[3]:.4f}; at 1024 rays: {devs[0]:.3f}")

# ---------------------------------------------------------------- summary
P("\n## Summary")
npass = sum(c[1] for c in checks)
P(f"{npass}/{len(checks)} checks passed")
for n, ok, d in checks:
    if not ok: P(f"FAILED: {n} -- {d}")
open(os.path.join(RES, "summary.md"), "w").write("\n".join(lines) + "\n")
json.dump([{"check": n, "pass": ok, "detail": d} for n, ok, d in checks], open(os.path.join(RES, "checks.json"), "w"), indent=1)
