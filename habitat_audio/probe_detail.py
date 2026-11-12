"""Finer analysis of the map probe from the stored roll-outs (runs/probe/*.npz), CPU only:
per-cell held-out AUROC maps (11 x 11, agent at the centre facing up), AUROC against distance from the agent, ahead vs behind,
and path-memory AUROC by time within the episode. Decoder: MLP on the GRU state, as in the paper.  python -m habitat_audio.probe_detail"""
import os, sys, json, glob, numpy as np, torch
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
from habitat_audio.probe_map import fit_probe, auroc, HALF, CELL
torch.set_num_threads(4); P = os.path.expanduser("~/steamaudio/habitat_audio/runs/probe/"); n = 2 * HALF + 1
ii, jj = np.meshgrid(np.arange(n) - HALF, np.arange(n) - HALF, indexing="ij"); fwd = ii.ravel() * CELL; lat = jj.ravel() * CELL; dist = np.hypot(fwd, lat); centre = HALF * n + HALF
AG = [("q6_sonar", "sonar image"), ("q6_sonar_beam", "sonar + learned beam"), ("q6_echo_scan", "head-scan binaural"), ("q6_blind", "blind")]; out = {}
for pre, name in AG:
    maps = {"occ": [], "vis": []}; bytime = []
    for f in sorted(glob.glob(f"{P}{pre}_s[0-9].npz")):
        D = np.load(f); Xtr, Xte = D["train_h"].astype(np.float32), D["held_h"].astype(np.float32); occ_te = D["held_occ"].reshape(len(Xte), -1).astype(bool); t = D["held_t"]
        for tgt in ("occ", "vis"):
            Ytr = D[f"train_{tgt}"].reshape(len(Xtr), -1).astype(np.float32); Yte = D[f"held_{tgt}"].reshape(len(Xte), -1).astype(np.float32)
            s = fit_probe(Xtr, Ytr, Xte, 256); a = auroc(Yte, s, occ_te if tgt == "vis" else None); a[centre] = np.nan; maps[tgt].append(a)
            if tgt == "vis":
                row = []
                for lo, hi in ((0, 50), (50, 150), (150, 301)):
                    k = (t >= lo) & (t < hi); aa = auroc(Yte[k], s[k], occ_te[k]); aa[centre] = np.nan; row.append(float(np.nanmean(aa)))
                bytime.append(row)
    M = {k: np.nanmean(np.array(v), 0) for k, v in maps.items()}; r = {}
    for k in ("occ", "vis"):
        m = M[k]; r[k] = {"map": [[None if np.isnan(x) else round(float(x), 3) for x in row] for row in m.reshape(n, n)],
                          "near(<=1m)": float(np.nanmean(m[(dist <= 1.0)])), "mid(1-2m)": float(np.nanmean(m[(dist > 1.0) & (dist <= 2.0)])), "far(>2m)": float(np.nanmean(m[dist > 2.0])),
                          "ahead": float(np.nanmean(m[fwd > 0])), "behind": float(np.nanmean(m[fwd < 0])), "directly_behind_1m": float(np.nanmean(m[(lat == 0) & (fwd < 0) & (fwd >= -1.0)])),
                          "directly_ahead_1m": float(np.nanmean(m[(lat == 0) & (fwd > 0) & (fwd <= 1.0)]))}
    r["vis_by_time"] = dict(zip(("steps 0-49", "steps 50-149", "steps 150-299"), np.mean(bytime, 0).round(3).tolist())); out[name] = r
    print(f"{name:22s} walkable: near {r['occ']['near(<=1m)']:.3f} mid {r['occ']['mid(1-2m)']:.3f} far {r['occ']['far(>2m)']:.3f} | ahead {r['occ']['ahead']:.3f} behind {r['occ']['behind']:.3f}", flush=True)
    print(f"{'':22s} path memory: near {r['vis']['near(<=1m)']:.3f} mid {r['vis']['mid(1-2m)']:.3f} far {r['vis']['far(>2m)']:.3f} | ahead {r['vis']['ahead']:.3f} behind {r['vis']['behind']:.3f} | 1 m directly behind {r['vis']['directly_behind_1m']:.3f}, directly ahead {r['vis']['directly_ahead_1m']:.3f} | by episode time {r['vis_by_time']}", flush=True)
json.dump(out, open(P + "probe_detail.json", "w"))
