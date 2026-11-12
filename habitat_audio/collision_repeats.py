"""Are collisions repeats? From ppo_eval --log-collisions files: the share of collisions that happen at the same place (within 5 cm)
and heading (within 5 deg) as an earlier collision of the same episode, split into immediate repeats (the previous step) and later
returns. python -m habitat_audio.collision_repeats file.json [file.json ...]"""
import sys, json, numpy as np
for f in sys.argv[1:]:
    eps = json.load(open(f)); n = imm = later = 0
    for ep in eps:
        for i, (st, x, z, h) in enumerate(ep):
            n += 1; prev = [(s2, x2, z2, h2) for (s2, x2, z2, h2) in ep[:i] if abs(x2 - x) < 0.05 and abs(z2 - z) < 0.05 and min(abs(h2 - h), 360 - abs(h2 - h)) < 5]
            if prev:
                if st - prev[-1][0] == 1: imm += 1
                else: later += 1
    print(f"{f}: {len(eps)} episodes, {n / max(len(eps), 1):.1f} collisions/episode; same place and heading as an earlier collision: {100 * (imm + later) / max(n, 1):.0f}% "
          f"(immediately repeated push {100 * imm / max(n, 1):.0f}%, returned later {100 * later / max(n, 1):.0f}%)")
