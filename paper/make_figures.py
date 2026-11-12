"""Regenerates every figure of the paper from the raw result files. Run in the `ss` conda env from the repository root:
    python paper/make_figures.py          (CPU only; the shoebox figure runs Steam Audio for a few seconds)"""
import os, sys, re, glob, json, csv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ.setdefault("STEAMAUDIO_LIB", ROOT + "/sdk/lib/patched_embree/libphonon.so"); os.environ.setdefault("STEAMAUDIO_EMBREE", "1")
from habitat_audio.audio_nav_env import compute_sonar, compute_range, AUDIO_SR, SONAR_BINS, ECHO_SECONDS, SteamAudioNavEnv
from pysteamaudio import steamaudio as sa
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = ROOT + "/habitat_audio/runs/"; F = ROOT + "/paper/figs/"; HELD = ["office_2", "frl_apartment_4", "hotel_0", "room_2"]
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3dd"
C = {"sonar": "#2a78d6", "sonar_beam": "#1baf7a", "echo_scan": "#6250d6", "blind": "#eb6834",
     "range_beam": "#eda100", "range_scan": "#e87ba4", "range_ahead": "#008300", "range_omni": "#e34948"}
plt.rcParams.update({"font.size": 8.5, "font.family": "DejaVu Sans", "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02})
pat = re.compile(r"^PPO greedy\s+coverage ([\d.]+) cells.*?collisions/episode ([\d.]+)")
def seeds(pre):
    out = []
    for d in sorted(glob.glob(R + pre + "_s[0-9]")):
        out.append(np.mean([[float(x) for x in pat.match(l).groups()] for sc in HELD for l in open(f"{d}/eval_{sc}.log") if pat.match(l)], 0))
    return np.array(out)

# ---------------------------------------------------------------- Fig: stock vs patched impulse response (single wall at 3 m)
def fig_ir():
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.2), sharey=False); T_TRUE = (np.sqrt(6.0 ** 2 + 2.0 ** 2) - 2.0) / 340 * 1e3   # image source at 6.32 m, direct path 2 m
    for ax, d, title, col in ((axs[0], "results", "(a) stock: 10 ms bins, noise", MUTED), (axs[1], "results_sparse", "(b) patched: 1-sample bins, sparse", C["sonar"])):
        m = json.load(open(f"{ROOT}/experiment/{d}/A_time_w3.json")); x = np.fromfile(f"{ROOT}/experiment/{d}/A_time_w3.f32", np.float32).reshape(m["numChannels"], -1)[0]
        t = np.arange(len(x)) / m["sr"] * 1e3; k = (t >= 0) & (t <= 45); ax.plot(t[k], x[k] / np.abs(x[k]).max(), color=col, lw=0.7)
        ax.axvline(T_TRUE, color="#e34948", lw=0.8, ls=(0, (3, 2))); ax.set_title(title, fontsize=8, color=INK, loc="left"); ax.set_xlabel("time after the direct-path arrival (ms)")
        ax.set_ylim(-1.15, 1.15)
    axs[0].set_ylabel("omnidirectional channel W\n(normalised)"); axs[1].text(T_TRUE + 0.8, 1.02, "image-source prediction:\n(6.32 m - 2 m) / 340 m/s = 12.72 ms", color="#b23030", fontsize=7.5, va="top")
    fig.savefig(F + "ir_stock_vs_patched.pdf"); plt.close(fig)

# ---------------------------------------------------------------- Fig: sonar image and range profiles in a shoebox
def fig_sonar():
    SIZE = (6.0, 3.0, 8.0); LIS = np.array([1.5, 1.0, -2.5]); AHEAD = np.array([0, 0, -1.0]); UP = np.array([0, 1.0, 0])
    V, T, _ = sa.box_room(SIZE, origin=(0, 0, -8.0)); ctx = sa.Context(); scene = sa.Scene(ctx)
    scene.add_mesh(V, T, [sa.Material.of((0.1, 0.2, 0.3), 0.05, (0.1, 0.05, 0.03))]); scene.commit()
    sim = sa.Simulator(ctx, scene, max_rays=16384, max_duration=0.3, max_order=1, sampling_rate=AUDIO_SR, frame_size=256, threads=4, max_sources=1); src = sim.add_source(); sim.commit()
    def click(aim=None, w=0.0, p=1.0, bounces=4):
        sim.set_listener(LIS, ahead=AHEAD, up=UP, num_rays=16384, bounces=bounces, duration=0.3, order=1, irradiance_min=0.1)
        src.set_inputs(LIS, ahead=AHEAD if aim is None else aim, up=UP, air_absorption=True, dipole_weight=w, dipole_power=p); sim.run_direct(); sim.run_reflections(); return sim.extract_ir(src, 0.3, 1)
    img = compute_sonar(click(), AHEAD, UP); m_bin = ECHO_SECONDS * 340 / 2 / SONAR_BINS[0]
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.7), gridspec_kw={"width_ratios": [0.7, 1.3, 1.15]})
    ax = axs[0]; ax.grid(False); ax.add_patch(plt.Rectangle((0, 0), 6, 8, fill=False, ec=INK, lw=1.2)); ax.plot([1.5], [2.5], "o", color=C["sonar"], ms=5)
    ax.annotate("", xy=(1.5, 3.7), xytext=(1.5, 2.6), arrowprops=dict(arrowstyle="-|>", color=C["sonar"], lw=1.2)); ax.text(1.75, 3.15, "heading", fontsize=7, color=INK)
    for (x, y, s, ha, va) in [(3.0, 8.15, "wall ahead, 5.5 m", "center", "bottom"), (3.0, -0.15, "wall behind, 2.5 m", "center", "top"), (-0.15, 4, "left wall, 1.5 m", "right", "center"), (6.15, 4, "right wall, 4.5 m", "left", "center")]:
        ax.text(x, y, s, fontsize=7, ha=ha, va=va, rotation=90 if ha != "center" else 0, color=INK)
    ax.set_xlim(-1.2, 7.2); ax.set_ylim(-1.3, 9.3); ax.set_aspect("equal"); ax.axis("off"); ax.set_title("(a) room, top view", fontsize=8, loc="left")
    ax = axs[1]; ax.grid(False); im = ax.imshow(img[:40, :, 0], origin="lower", aspect="auto", cmap="Blues", extent=[-180, 180, 0, 40 * m_bin])
    ax.set_xticks([-180, -90, 0, 90, 180]); ax.set_xticklabels(["behind", "right", "ahead", "left", "behind"]); ax.set_xlabel("direction of arrival (body frame)"); ax.set_ylabel("range (m)")
    for az, d, s, tx, ty in [(0, 5.5, "ahead wall", -40, 7.4), (90, 1.5, "left wall", 20, 0.35), (-90, 4.5, "right wall", -170, 3.3), (174, 2.5, "wall behind", 60, 4.6)]:
        ax.annotate(s, xy=(az, d), xytext=(tx, ty), fontsize=6.8, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax.set_title("(b) sonar image, channel 0", fontsize=8, loc="left"); cb = fig.colorbar(im, ax=ax, pad=0.02, fraction=0.05); cb.set_label("log(1 + 10 x amplitude)", fontsize=7); cb.outline.set_visible(False)
    ax = axs[2]; r_ax = (np.arange(SONAR_BINS[0]) + 0.5) * m_bin
    for name, yaw, col, d in [("aimed 90 deg left", 90, C["sonar"], 1.5), ("aimed ahead", 0, C["blind"], 5.5), ("aimed 90 deg right", -90, C["sonar_beam"], 4.5)]:
        prof = compute_range(click(SteamAudioNavEnv.rotated(AHEAD, UP, yaw), 0.5, 8.0, bounces=1)); k = r_ax <= 7; ax.plot(r_ax[k], prof[k], color=col, lw=1.3, label=name)
        j = int(np.argmax(prof)); ax.plot([r_ax[j]], [prof[j]], "o", color=col, ms=4, mec="white", mew=0.8); ax.text(r_ax[j] + 0.12, prof[j] + 0.03, f"{r_ax[j]:.1f} m", fontsize=7, color=INK)
    ax.set_xlabel("range (m)"); ax.set_ylabel("log(1 + 10 x amplitude)"); ax.set_ylim(0, 3.4); ax.legend(frameon=False, fontsize=7, loc="upper right"); ax.set_title("(c) range-only profiles", fontsize=8, loc="left")
    fig.tight_layout(w_pad=0.6); fig.savefig(F + "sonar_shoebox.pdf"); plt.close(fig)

# ---------------------------------------------------------------- Fig: seed dot plots
def dots(agents, fname, bump, width=6.8):
    fig, axs = plt.subplots(1, 2, figsize=(width, 2.5))
    for j, (ax, lab, bt) in enumerate(zip(axs, ["coverage (0.5 m cells per 300-step episode)", "collisions per 300-step episode"], bump)):
        for i, (pre, name, col) in enumerate(agents):
            v = seeds(pre)[:, j]; ax.barh(i, v.mean(), height=0.56, color=col, alpha=0.30, lw=0); ax.plot(v, np.full(len(v), i), "o", color=col, ms=5, mec="white", mew=0.8, zorder=3)
            ax.text(max(v.max(), v.mean()) + (0.9 if j == 0 else 1.1), i, f"{v.mean():.1f}", va="center", fontsize=7.5, color=INK)
        ax.axvline(bt, color=MUTED, lw=0.9, ls=(0, (3, 2))); ax.text(bt, -0.55, f" bump-and-turn {bt} ", fontsize=7, color=MUTED, ha="left" if j == 0 else "right", va="center")
        ax.set_yticks(range(len(agents))); ax.set_yticklabels([a[1] for a in agents] if j == 0 else []); ax.invert_yaxis(); ax.set_xlabel(lab); ax.grid(axis="y", visible=False); ax.set_xlim(0, None); ax.set_ylim(len(agents) - 0.5, -0.9)
    fig.tight_layout(w_pad=1.2); fig.savefig(F + fname); plt.close(fig)

# ---------------------------------------------------------------- Fig: learning curves (mean and s.d. over seeds)
def fig_curves():
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.5))
    for pre, name, col in [("q6_sonar", "sonar image", C["sonar"]), ("q6_sonar_beam", "sonar + learned beam", C["sonar_beam"]), ("q6_echo_scan", "head-scan binaural", C["echo_scan"]), ("q6_blind", "blind", C["blind"])]:
        Y = []
        for d in sorted(glob.glob(R + pre + "_s[0-9]")):
            rows = {}
            for r in csv.DictReader(open(d + "/log.csv")):
                try: rows[int(r["steps"])] = (float(r["coverage_cells"]), float(r["collisions"]))
                except ValueError: pass
            s = np.array(sorted(rows)); v = np.array([rows[k] for k in s]); g = np.linspace(5e4, 2e6, 80); Y.append(np.stack([np.interp(g, s[~np.isnan(v[:, i])], v[~np.isnan(v[:, i]), i]) for i in (0, 1)]))
        Y = np.array(Y)
        for i, ax in enumerate(axs):
            mu, sd = Y[:, i].mean(0), Y[:, i].std(0); ax.fill_between(g / 1e6, mu - sd, mu + sd, color=col, alpha=0.18, lw=0); ax.plot(g / 1e6, mu, color=col, lw=1.4, label=name)
            if i == 0: ax.text(2.02, mu[-1], name, color=INK, fontsize=7, va="center")
    axs[0].set_ylabel("training coverage (cells)"); axs[1].set_ylabel("training collisions / episode"); axs[1].set_ylim(0, 100)
    for ax in axs: ax.set_xlabel("environment steps (millions)")
    axs[0].set_xlim(0, 2.75); axs[0].set_xticks([0, 0.5, 1, 1.5, 2]); axs[1].legend(frameon=False, fontsize=7)
    fig.tight_layout(w_pad=1.2); fig.savefig(F + "learning_curves.pdf"); plt.close(fig)

# ---------------------------------------------------------------- Fig: probe
def fig_probe():
    P = R + "probe/"; ag = [("q6_sonar", "sonar image"), ("q6_sonar_beam", "sonar +\nlearned beam"), ("q6_echo_scan", "head-scan\nbinaural"), ("q6_blind", "blind")]
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.5), sharey=True)
    for ax, key, title in ((axs[0], "occ/{}/mlp", "(a) local geometry: is the cell walkable?"), (axs[1], "vis/{}/mlp/navigable", "(b) path memory: was this walkable cell visited?")):
        for i, (pre, name) in enumerate(ag):
            J = [json.load(open(f)) for f in sorted(glob.glob(f"{P}{pre}_s[0-9]_probe.json"))]
            for k, (src, col, off) in enumerate((("memory", C["sonar"], -0.19), ("observation", C["blind"], 0.19))):
                v = np.array([j[key.format(src)]["auroc"] for j in J]); ax.bar(i + off, v.mean() - 0.5, bottom=0.5, width=0.34, color=col, alpha=0.30, lw=0)
                ax.plot(np.full(len(v), i + off), v, "o", color=col, ms=4, mec="white", mew=0.7, zorder=3); ax.text(i + off, v.max() + 0.012, f"{v.mean():.2f}", ha="center", fontsize=7, color=INK)
        ax.axhline(0.5, color=MUTED, lw=0.9, ls=(0, (3, 2))); ax.set_xticks(range(len(ag))); ax.set_xticklabels([a[1] for a in ag], fontsize=7.5); ax.set_title(title, fontsize=8, loc="left"); ax.grid(axis="x", visible=False); ax.set_ylim(0.45, 0.92)
    axs[0].set_ylabel("held-out AUROC (0.5 = chance)")
    axs[0].plot([], [], "s", color=C["sonar"], alpha=0.6, label="decoded from recurrent state"); axs[0].plot([], [], "s", color=C["blind"], alpha=0.6, label="decoded from current observation"); fig.legend(*axs[0].get_legend_handles_labels(), frameon=False, fontsize=7.5, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout(w_pad=1.0); fig.savefig(F + "probe.pdf"); plt.close(fig)

if __name__ == "__main__":
    os.makedirs(F, exist_ok=True); fig_ir(); fig_sonar()
    dots([("q6_sonar", "sonar image, fixed click", C["sonar"]), ("q6_sonar_beam", "sonar image + learned beam", C["sonar_beam"]), ("q6_echo_scan", "head-scan binaural", C["echo_scan"]), ("q6_blind", "blind (bump sensor)", C["blind"])], "exp1_sensors.pdf", (28.0, 31.8))
    dots([("q6_sonar", "sonar image (Exp. 1)", C["sonar"]), ("q7_range_ahead", "range + fixed ahead beam", C["range_ahead"]), ("q7_range_scan", "range + scripted sweep", C["range_scan"]), ("q7_range_omni", "range + omni click", C["range_omni"]),
          ("q7_range_beam", "range + learned beam", C["range_beam"]), ("q6_blind", "blind (Exp. 1)", C["blind"])], "exp2_range.pdf", (28.0, 31.8))
    fig_curves(); fig_probe(); print("figures written to", F)
