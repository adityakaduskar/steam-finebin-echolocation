"""Writes figs/tab_per_building.tex (per-building, per-seed held-out results) from figs/per_building.json (made from the eval logs)."""
import json, os, numpy as np
D = json.load(open(os.path.dirname(os.path.abspath(__file__)) + "/figs/per_building.json"))
names = {"q6_sonar": "Sonar image, fixed click", "q6_sonar_beam": "Sonar image + learned beam", "q6_echo_scan": "Head-scan binaural", "q6_blind": "Blind, no auxiliary loss", "q9_blind_aux": "Blind + auxiliary loss", "q9_sonar_beam_fwd": "Sonar + learned forward beams",
         "q7_range_beam": "Range + learned beam", "q7_range_scan": "Range + scripted sweep", "q7_range_ahead": "Range + fixed ahead beam", "q7_range_omni": "Range + omni click"}
bld = {"office_2": "office\\_2", "frl_apartment_4": "frl\\_apartment\\_4", "hotel_0": "hotel\\_0", "room_2": "room\\_2"}
L = ["\\begin{tabular}{llrrrrrrrr}", "\\toprule", " & & \\multicolumn{4}{c}{Coverage (cells)} & \\multicolumn{4}{c}{Collisions per episode} \\\\",
     "\\cmidrule(lr){3-6}\\cmidrule(lr){7-10}", "Agent & Building & seed 1 & seed 2 & seed 3 & mean & seed 1 & seed 2 & seed 3 & mean \\\\", "\\midrule"]
for a, nm in names.items():
    for i, (b, bn) in enumerate(bld.items()):
        g = D[a][b]; cov = [x[0] for x in g]; col = [x[2] for x in g]
        L.append(f"{nm if i == 0 else ''} & {bn} & " + " & ".join(f"{v:.1f}" for v in cov) + f" & {np.mean(cov):.1f} & " + " & ".join(f"{v:.1f}" for v in col) + f" & {np.mean(col):.1f} \\\\")
    if a != "q7_range_omni": L.append("\\addlinespace")
L += ["\\bottomrule", "\\end{tabular}"]
open(os.path.dirname(os.path.abspath(__file__)) + "/figs/tab_per_building.tex", "w").write("\n".join(L) + "\n"); print("ok")

# ---- Experiment 4: memory wipe table (figs/tab_wipe.tex) from <run>/wipe<N>_<scene>.log
import re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/habitat_audio/runs/"
pat = re.compile(r"^PPO greedy.*?coverage ([\d.]+) cells.*?path ([\d.]+) m\s+collisions/episode ([\d.]+)")
def wipe(pre, n):
    per = []
    for s in (1, 2, 3):
        v = []
        for sc in ("office_2", "hotel_0"):
            p = f"{R}{pre}_s{s}/wipe{n}_{sc}.log"
            if os.path.exists(p):
                v += [[float(x) for x in m.groups()] for m in map(pat.match, open(p)) if m]
        if len(v) == 2: per.append(np.mean(v, 0))
    return np.array(per)
L = ["\\begin{tabular}{lccc}", "\\toprule", "Agent & Memory intact & Erased every 20 steps & Erased every step \\\\", "\\midrule"]
for pre, nm in [("q6_blind", "Blind"), ("q6_sonar", "Sonar image, fixed click"), ("q6_sonar_beam", "Sonar image + learned beam"), ("q7_range_beam", "Range + learned beam")]:
    cells = []
    for n in (0, 20, 1):
        v = wipe(pre, n); print(pre, n, len(v), np.round(v[:, 0], 1), np.round(v[:, 2], 1), "path", np.round(v[:, 1].mean(), 1))
        cells.append(f"\\pmsd{{{v[:,0].mean():.1f}}}{{{v[:,0].std():.1f}}} / \\pmsd{{{v[:,2].mean():.1f}}}{{{v[:,2].std():.1f}}} / {v[:,1].mean():.1f}" if len(v) == 3 else "pending")
    L.append(f"{nm} & " + " & ".join(cells) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(os.path.dirname(os.path.abspath(__file__)) + "/figs/tab_wipe.tex", "w").write("\n".join(L) + "\n")
