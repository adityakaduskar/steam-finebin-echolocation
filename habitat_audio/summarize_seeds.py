"""Aggregate queue 6 held-out evaluations over seeds: mean and spread of greedy/sampled coverage and collisions per agent."""
import re, glob, os, numpy as np, sys
R = os.path.expanduser("~/steamaudio/habitat_audio/runs/"); HELD = ["office_2", "frl_apartment_4", "hotel_0", "room_2"]
AGENTS = [("q6_sonar", "sonar, fixed click"), ("q6_sonar_beam", "sonar + learned beam"), ("q6_echo_scan", "head-scan binaural"), ("q6_blind", "blind")]
if len(sys.argv) > 1: AGENTS = [tuple(a.split(":", 1)) for a in sys.argv[1].split(",")]   # "prefix:label,prefix:label"
pat = re.compile(r"^(PPO greedy|PPO sample|bump-turn)\s+coverage ([\d.]+) cells.*collisions/episode ([\d.]+)")
def read(path):
    out = {}
    for l in open(path):
        m = pat.match(l)
        if m: out[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return out
rows = ["| agent | seeds | greedy coverage | greedy collisions/ep | sampled coverage | sampled collisions/ep |", "|---|---|---|---|---|---|"]
for pre, name in AGENTS:
    per_seed = {"PPO greedy": [], "PPO sample": []}
    for d in sorted(glob.glob(R + pre + "_s[0-9]")):
        res = [read(f"{d}/eval_{sc}.log") for sc in HELD if os.path.exists(f"{d}/eval_{sc}.log")]
        if len(res) < len(HELD) or any("PPO greedy" not in r for r in res): continue
        for k in per_seed: per_seed[k].append(np.mean([r[k] for r in res], 0))   # mean over buildings -> (coverage, collisions)
    n = len(per_seed["PPO greedy"])
    if n == 0: rows.append(f"| {name} | 0 | | | | |"); continue
    f = lambda k, i: f"{np.mean([x[i] for x in per_seed[k]]):.1f} ± {np.std([x[i] for x in per_seed[k]]):.1f}"
    rows.append(f"| {name} | {n} | {f('PPO greedy',0)} | {f('PPO greedy',1)} | {f('PPO sample',0)} | {f('PPO sample',1)} |")
bt = [read(p).get("bump-turn") for pre, _ in AGENTS for p in glob.glob(R + pre + "_s1/eval_*.log")]; bt = [b for b in bt if b]
if bt: rows.append(f"| bump-and-turn heuristic | | {np.mean([b[0] for b in bt]):.1f} | {np.mean([b[1] for b in bt]):.1f} | | |")
print("\n".join(rows)); print("\n(mean over the 4 held-out buildings per seed; ± = standard deviation across seeds)")
