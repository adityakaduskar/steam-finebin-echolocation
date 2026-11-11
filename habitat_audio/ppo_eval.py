#!/usr/bin/env python3
"""Evaluate a trained policy against random and oracle agents on the same episodes. python -m habitat_audio.ppo_eval --ckpt ... --episodes 100"""
import os, sys, argparse, json, time
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
_EMB = os.path.expanduser("~/steamaudio/sdk/lib/patched_embree/libphonon.so")   # default to the Embree build when present (same physics, faster)
if os.path.exists(_EMB): os.environ.setdefault("STEAMAUDIO_LIB", _EMB); os.environ.setdefault("STEAMAUDIO_EMBREE", "1")
import numpy as np, torch
from habitat_audio import SteamAudioNavEnv, STOP
from habitat_audio.ppo_train import Policy, SCENE, SCENES, ENV_KW, to_tensor, load_policy, greedy

def run(env, episodes, act_fn, name):
    stats = []; beam_counts = np.zeros(len(env.beams)) if env.beams else None
    for i, (start, goal) in enumerate(episodes):
        obs = env.reset(start=start, goal=goal, sound="telephone.wav", heading_deg=float(i * 37 % 360)); done = False; state = act_fn("init"); info = {}
        while not done:
            a, state = act_fn((obs, state, env)); obs, r, done, info = env.step(a)
            if beam_counts is not None: beam_counts[info["beam"]] += 1
        stats.append((info["success"], info["spl"], info["step"], env.episode["geodesic"], info.get("collisions", 0), info.get("coverage_cells", 0), info.get("path_length", 0), info.get("clicks", 0)))
    s = np.array(stats, float); clicks = f"  clicks/step {s[:,7].sum()/max(s[:,2].sum(),1):.2f}  beams " + " ".join(f"{b[0]} {c / max(beam_counts.sum(), 1):.2f}" for b, c in zip(env.beams, beam_counts)) if env.beams else ""
    if env.explore: print(f"{name:10s} coverage {s[:,5].mean():.1f} cells ({s[:,5].mean()*env.coverage_cell**2:.1f} m^2)  path {s[:,6].mean():.1f} m  collisions/episode {s[:,4].mean():.1f}  collisions/m {s[:,4].sum()/max(s[:,6].sum(),1e-9):.2f}{clicks}", flush=True)
    else: print(f"{name:10s} success {s[:,0].mean():.2f}  SPL {s[:,1].mean():.2f}  mean length {s[:,2].mean():.0f}  collisions/episode {s[:,4].mean():.1f}{clicks}", flush=True)
    return s

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ckpt", default="habitat_audio/runs/ppo_apartment1/checkpoint.pt"); ap.add_argument("--episodes", type=int, default=100)
    ap.add_argument("--geodesic", type=float, nargs=2, default=(1.0, 8.0)); ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--ablate", default=None, choices=[None, "shuffled", "zeros"], help="replace the echo observation at test time: shuffled = an echo recorded at a random other pose, zeros = none")
    ap.add_argument("--skip-baselines", action="store_true"); ap.add_argument("--scene", default="apartment_1", help="scene name (see SCENES) or path"); args = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu"); ck = torch.load(args.ckpt, map_location=device)
    kw = dict(ck.get("env_kw", ENV_KW)); kw["geodesic_range"] = tuple(args.geodesic); kw["threads"] = 8; keys = ck.get("keys", ["spectrogram"])
    kw.pop("aux_directions", None); kw.pop("echo_dropout", None); scene = SCENES.get(args.scene, args.scene); print("evaluating on", os.path.basename(scene), flush=True)
    env = SteamAudioNavEnv(scene, seed=args.seed, **kw)
    episodes = [env.sample_episode()[:2] for _ in range(args.episodes)]
    policy, keys = load_policy(ck, device); nb = policy.n_beams
    echo_bank = None; ekey = "sonar" if "sonar" in keys else "echo"
    if args.ablate == "shuffled" and ekey in keys:   # bank of echoes from 300 random poses
        echo_bank = []
        for _ in range(300):
            env.reset(); env.step(int(np.random.randint(1, 4))); echo_bank.append(env._observe()[ekey])
        rs = np.random.RandomState(0)
    def ablate(obs):
        if args.ablate is None or ekey not in obs: return obs
        obs = dict(obs); obs[ekey] = echo_bank[rs.randint(len(echo_bank))] if args.ablate == "shuffled" else np.zeros_like(obs[ekey]); return obs
    def ppo_act(x, use_greedy):
        if x == "init": return (torch.zeros(1, 512, device=device), torch.full((1,), 4, dtype=torch.long, device=device), torch.full((1,), nb, dtype=torch.long, device=device) if nb else None)
        obs, (h, pa, pb), _ = x
        with torch.no_grad(): dist, v, h = policy.step(to_tensor([ablate(obs)], device, keys), pa, h, torch.ones(1, device=device), pb)
        a = greedy(dist) if use_greedy else dist.sample()
        if nb: return (int(a[0, 0]), int(a[0, 1])), (h, a[:, 0], a[:, 1])
        return int(a.item()), (h, a, None)
    def rand_act(x):
        if x == "init": return 0
        obs, n, env = x; a = int(np.random.randint(4))
        if a == STOP and n < 20: a = 1
        return a, n + 1
    def bump_act(x):   # scripted bump-and-turn: forward until a collision, then turn 30-90 deg
        if x == "init": return 0
        obs, turns_left, env = x
        if turns_left > 0: return 2, turns_left - 1
        if env.last_collided: return 2, int(np.random.randint(2, 9))
        return 1, 0
    def oracle_act(x):
        if x == "init": return None
        try: return x[2].oracle_action(), None
        except Exception: return 0, None   # habitat_sim GreedyFollowerError: count the episode as a failure (stop)
    tag = f" [echo {args.ablate}]" if args.ablate else ""
    res = {"ppo_greedy": run(env, episodes, lambda x: ppo_act(x, True), "PPO greedy" + tag), "ppo_sample": run(env, episodes, lambda x: ppo_act(x, False), "PPO sample" + tag)}
    if not args.skip_baselines:
        res["random"] = run(env, episodes, rand_act, "random")
        if env.explore: res["bump_turn"] = run(env, episodes, bump_act, "bump-turn")
        else: res["oracle"] = run(env, episodes, oracle_act, "oracle")
    json.dump({k: v.tolist() for k, v in res.items()}, open(os.path.join(os.path.dirname(args.ckpt), f"eval_{args.episodes}{'_' + args.ablate if args.ablate else ''}{'' if args.scene == 'apartment_1' else '_' + os.path.basename(scene).split('.')[0]}.json"), "w"))
    env.close()

if __name__ == "__main__": main()
