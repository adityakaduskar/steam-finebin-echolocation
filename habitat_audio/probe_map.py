#!/usr/bin/env python3
"""Map-building probe: does a trained explorer's recurrent state contain a map of its surroundings?

1. collect: roll out a trained policy (sampled actions) in the training buildings and in the held-out buildings; at every step record
   the GRU state h_t, a pooled copy of the current echo observation, the contact bit, and two egocentric labels on an 11 x 11 grid
   of 0.5 m cells around the agent: 'occ' (navigable floor, i.e. the local geometry) and 'vis' (already visited this episode,
   i.e. episodic memory, which no single observation contains).
2. fit: train linear and MLP decoders on the training-building samples and test them on the held-out buildings. Report per-cell
   AUROC averaged over cells, for decoders reading (a) the memory state h_t, (b) only the current observation.

python -m habitat_audio.probe_map collect --ckpt runs/q6_sonar_s1/checkpoint.pt --out runs/probe/q6_sonar_s1.npz
python -m habitat_audio.probe_map fit --data runs/probe/q6_sonar_s1.npz
"""
import os, sys, argparse, json, time
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F

TRAIN = ["apartment_0", "apartment_1", "apartment_2", "frl_apartment_0", "frl_apartment_1", "frl_apartment_2", "frl_apartment_3",
         "frl_apartment_5", "office_0", "office_1", "office_3", "office_4", "room_0", "room_1"]
HELD = ["office_2", "frl_apartment_4", "hotel_0", "room_2"]
HALF, CELL = 5, 0.5


def pooled_obs(obs, keys):
    """current-observation features for the baseline decoder: echo/sonar observation average-pooled to <= 512 numbers, plus contact"""
    parts = []
    for k in keys:
        x = np.asarray(obs[k], np.float32)
        if x.ndim == 3:   # (H, W, C) image-like
            t = torch.as_tensor(x).permute(2, 0, 1)[None]; t = F.adaptive_avg_pool2d(t, (16, 16 // max(1, x.shape[2] // 2))); parts.append(t.flatten().numpy())
        else: parts.append(x.ravel())
    return np.concatenate(parts).astype(np.float32)


def collect(args):
    from habitat_audio.ppo_train import SCENES, load_policy, to_tensor, VECTOR_KEYS
    from habitat_audio.vec_env import SubprocVecEnv
    device = torch.device("cpu"); torch.set_num_threads(4)
    ck = torch.load(args.ckpt, map_location=device); policy, keys = load_policy(ck, device); nb = policy.n_beams
    kw = dict(ck["env_kw"]); [kw.pop(k, None) for k in ("aux_directions", "echo_dropout")]; kw["probe_grid"] = (HALF, CELL); kw["threads"] = 1
    out = {}
    for split, names, steps in (("train", TRAIN, args.train_steps), ("held", HELD, args.held_steps)):
        venv = SubprocVecEnv([SCENES["replica/" + n] for n in names], len(names), kw, seed=args.seed); obs = venv.reset(); N = len(names)
        h = torch.zeros(N, 512); pa = torch.full((N,), 4, dtype=torch.long); pb = torch.full((N,), nb, dtype=torch.long) if nb else None
        mask = torch.ones(N); prev_info = [None] * N; H, X, OCC, VIS, T, S = [], [], [], [], [], []; t0 = time.time()
        for step in range(steps):
            with torch.no_grad(): dist, _, h = policy.step(to_tensor(obs, device, keys), pa, h, mask, pb)
            for e in range(N):
                if prev_info[e] is not None:   # labels describe the pose at which obs[e] was taken
                    H.append(h[e].numpy().astype(np.float16)); X.append(pooled_obs(obs[e], keys).astype(np.float16))
                    OCC.append(prev_info[e]["occ"]); VIS.append(prev_info[e]["vis"]); T.append(prev_info[e]["step"]); S.append(e)
            a = dist.sample(); obs, rew, done, infos = venv.step(a.numpy())
            a_nav = a[:, 0] if nb else a; d = torch.as_tensor(done)
            pa = torch.where(d, torch.full_like(a_nav, 4), a_nav); mask = (~d).float()
            if nb: pb = torch.where(d, torch.full_like(a_nav, nb), a[:, 1])
            prev_info = [None if done[e] else infos[e] for e in range(N)]
            if step % 500 == 0: print(f"{split} step {step}/{steps}  samples {len(H)}  {time.time() - t0:.0f} s", flush=True)
        venv.close()
        out.update({f"{split}_h": np.stack(H), f"{split}_x": np.stack(X), f"{split}_occ": np.stack(OCC), f"{split}_vis": np.stack(VIS),
                    f"{split}_t": np.array(T), f"{split}_scene": np.array(S)})
    os.makedirs(os.path.dirname(args.out), exist_ok=True); np.savez_compressed(args.out, **out, keys=np.array(keys)); print("saved", args.out)


def auroc(y, s, mask=None):
    """per-column AUROC (rank formulation); NaN for columns with one class. mask (same shape, bool) restricts the samples per column"""
    res = []
    for j in range(y.shape[1]):
        yj, sj = y[:, j], s[:, j]
        if mask is not None: yj, sj = yj[mask[:, j]], sj[mask[:, j]]
        P = yj.sum(); Nn = len(yj) - P
        if P == 0 or Nn == 0: res.append(np.nan); continue
        r = np.empty(len(sj)); r[np.argsort(sj, kind="mergesort")] = np.arange(1, len(sj) + 1)
        res.append((r[yj == 1].sum() - P * (P + 1) / 2) / (P * Nn))
    return np.array(res)


def fit_probe(Xtr, Ytr, Xte, hidden, epochs=15, seed=0):
    torch.manual_seed(seed); mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    xtr = torch.as_tensor((Xtr - mu) / sd, dtype=torch.float32); ytr = torch.as_tensor(Ytr, dtype=torch.float32); xte = torch.as_tensor((Xte - mu) / sd, dtype=torch.float32)
    d = xtr.shape[1]; m = nn.Linear(d, ytr.shape[1]) if hidden == 0 else nn.Sequential(nn.Linear(d, hidden), nn.ReLU(), nn.Linear(hidden, ytr.shape[1]))
    opt = torch.optim.Adam(m.parameters(), lr=1e-3, weight_decay=1e-4); n = len(xtr)
    for _ in range(epochs):
        perm = torch.randperm(n)
        for i in range(0, n, 512):
            b = perm[i:i + 512]; loss = F.binary_cross_entropy_with_logits(m(xtr[b]), ytr[b]); opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): return m(xte).numpy()


def fit(args):
    D = np.load(args.data); n = 2 * HALF + 1; centre = HALF * n + HALF
    rows = np.repeat(np.arange(n) - HALF, n)   # forward offset of each flattened cell (negative = behind)
    res = {}
    for target in ("occ", "vis"):
        Ytr = D[f"train_{target}"].reshape(len(D["train_occ"]), -1).astype(np.float32); Yte = D[f"held_{target}"].reshape(len(D["held_occ"]), -1).astype(np.float32)
        keep = np.ones(n * n, bool); keep[centre] = False   # the agent's own cell is trivially navigable / visited
        for src in ("h", "x"):
            Xtr = D[f"train_{src}"].astype(np.float32); Xte = D[f"held_{src}"].astype(np.float32)
            for hidden in (0, 256):
                s = fit_probe(Xtr, Ytr, Xte, hidden); a = auroc(Yte[:, keep], s[:, keep]); fr = rows[keep]
                key = f"{target}/{'memory' if src == 'h' else 'observation'}/{'linear' if hidden == 0 else 'mlp'}"
                if target == "vis":   # visited cells are always navigable: score memory only among navigable cells, so geometry cannot stand in for it
                    occ_te = D["held_occ"].reshape(len(D["held_occ"]), -1)[:, keep].astype(bool); an = auroc(Yte[:, keep], s[:, keep], occ_te)
                    res[key + "/navigable"] = {"auroc": float(np.nanmean(an)), "auroc_front": float(np.nanmean(an[fr > 0])), "auroc_behind": float(np.nanmean(an[fr < 0])), "base_rate": float(Yte[:, keep][occ_te].mean())}
                    print(f"{os.path.basename(args.data):28s} {key + '/navigable':32s} AUROC {res[key + '/navigable']['auroc']:.3f}", flush=True)
                res[key] = {"auroc": float(np.nanmean(a)), "auroc_front": float(np.nanmean(a[fr > 0])), "auroc_behind": float(np.nanmean(a[fr < 0])),
                            "base_rate": float(Yte[:, keep].mean())}
                print(f"{os.path.basename(args.data):28s} {key:32s} AUROC {res[key]['auroc']:.3f}  (ahead {res[key]['auroc_front']:.3f}, behind {res[key]['auroc_behind']:.3f})  base rate {res[key]['base_rate']:.2f}", flush=True)
    json.dump(res, open(args.data.replace(".npz", "_probe.json"), "w"), indent=1)


def summary(args):
    """mean +- s.d. over seeds of held-out AUROC, per agent, target and decoder -> markdown"""
    import glob, re
    agents = [("q6_sonar", "sonar, fixed click"), ("q6_sonar_beam", "sonar + learned beam"), ("q6_echo_scan", "head-scan binaural"), ("q6_blind", "blind")]
    lines = ["| agent | target | decoder | memory state h_t | current observation only |", "|---|---|---|---|---|"]
    for pre, name in agents:
        R = [json.load(open(f)) for f in sorted(glob.glob(f"{args.dir}/{pre}_s[0-9]_probe.json"))]
        if not R: continue
        for tgt, tname, suf in (("occ", "local geometry", ""), ("vis", "visited", ""), ("vis", "visited, among walkable cells (memory)", "/navigable")):
            for dec in ("linear", "mlp"):
                f = lambda src: (lambda v: f"{np.mean(v):.3f} ± {np.std(v):.3f}")([r[f"{tgt}/{src}/{dec}{suf}"]["auroc"] for r in R])
                lines.append(f"| {name} (n={len(R)}) | {tname} | {dec} | {f('memory')} | {f('observation')} |")
    txt = "\n".join(lines) + "\n\nHeld-out-building AUROC averaged over the 120 non-centre cells of an 11 x 11 egocentric grid (0.5 m); 0.5 = chance."
    print(txt); open(f"{args.dir}/probe_summary.md", "w").write(txt + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["collect", "fit", "summary"]); ap.add_argument("--dir", default=os.path.expanduser("~/steamaudio/habitat_audio/runs/probe")); ap.add_argument("--ckpt"); ap.add_argument("--out"); ap.add_argument("--data")
    ap.add_argument("--train-steps", type=int, default=3000); ap.add_argument("--held-steps", type=int, default=6000); ap.add_argument("--seed", type=int, default=777)
    a = ap.parse_args(); {"collect": collect, "fit": fit, "summary": summary}[a.cmd](a)
