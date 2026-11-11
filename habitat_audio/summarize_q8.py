"""Queue 8 tables: (A) memory wipe -- held-out greedy coverage/collisions per agent and wipe interval; (B) click-cost sweep with clicks/step."""
import re, glob, os, numpy as np
R = os.path.expanduser("~/steamaudio/habitat_audio/runs/")
pat = re.compile(r"^PPO greedy.*?coverage ([\d.]+) cells.*collisions/episode ([\d.]+)(?:.*clicks/step ([\d.]+))?")
def read(path):
    if not os.path.exists(path): return None
    for l in open(path):
        m = pat.match(l)
        if m: return [float(m.group(1)), float(m.group(2)), float(m.group(3)) if m.group(3) else np.nan]
    return None
def ms(v): return f"{np.mean(v):.1f} ± {np.std(v):.1f}"
out = ["### A. Memory wipe (held-out office_2 + hotel_0, greedy, 30 episodes each; mean ± s.d. over 3 seeds)", "",
       "| agent | memory kept | wiped every 20 steps | wiped every step (no memory) |", "|---|---|---|---|"]
for pre, name in [("q6_sonar", "sonar image"), ("q6_sonar_beam", "sonar + learned beam"), ("q7_range_beam", "range + learned beam"), ("q6_blind", "blind")]:
    cells = []
    for n in (0, 20, 1):
        per = []
        for d in sorted(glob.glob(R + pre + "_s[0-9]")):
            v = [read(f"{d}/wipe{n}_{sc}.log") for sc in ("office_2", "hotel_0")]
            if all(v): per.append(np.mean([x[:2] for x in v], 0))
        cells.append(f"{ms([p[0] for p in per])} cells, {ms([p[1] for p in per])} coll" if per else "–")
    out.append(f"| {name} | " + " | ".join(cells) + " |")
out += ["", "### B. Click-cost sweep, range + learned beam (held-out 4 buildings, greedy; mean ± s.d. over 3 seeds)", "",
        "| click cost | coverage (cells) | collisions / episode | clicks / step |", "|---|---|---|---|"]
for cost, pre in [("0", "q8_range_beam_c0"), ("0.01 (queue 7)", "q7_range_beam"), ("0.03", "q8_range_beam_c003"), ("0.1", "q8_range_beam_c01")]:
    per = []
    for d in sorted(glob.glob(R + pre + "_s[0-9]")):
        v = [read(f"{d}/eval_{sc}.log") for sc in ("office_2", "frl_apartment_4", "hotel_0", "room_2")]
        if all(v): per.append(np.nanmean(v, 0))
    if per: out.append(f"| {cost} | {ms([p[0] for p in per])} | {ms([p[1] for p in per])} | {np.mean([p[2] for p in per]):.2f} ({', '.join(f'{p[2]:.2f}' for p in per)}) |")
print("\n".join(out))
