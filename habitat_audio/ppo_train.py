#!/usr/bin/env python3
"""Recurrent PPO (audio-only, SoundSpaces-style AudioCNN + GRU) on SteamAudioNavEnv.
python -m habitat_audio.ppo_train --steps 600000 --envs 8 --out habitat_audio/runs/ppo_apartment1"""
import os, sys, time, json, argparse, math
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F

SCENE = os.path.expanduser("~/sound-spaces/data/versioned_data/habitat_test_scenes_1.0/apartment_1.glb")
_HTS = os.path.expanduser("~/sound-spaces/data/versioned_data/habitat_test_scenes_1.0/")
SCENES = {"apartment_1": _HTS + "apartment_1.glb", "van-gogh-room": _HTS + "van-gogh-room.glb", "skokloster-castle": _HTS + "skokloster-castle.glb",
          "17DRP5sb8fy": os.path.expanduser("~/sound-spaces/data/scene_datasets/mp3d_example/17DRP5sb8fy/17DRP5sb8fy.glb")}
_REP = os.path.expanduser("~/sound-spaces/data/scene_datasets/Replica-Dataset/")
REPLICA = ["apartment_0", "apartment_1", "apartment_2", "frl_apartment_0", "frl_apartment_1", "frl_apartment_2", "frl_apartment_3", "frl_apartment_4", "frl_apartment_5",
           "hotel_0", "office_0", "office_1", "office_2", "office_3", "office_4", "room_0", "room_1", "room_2"]
SCENES.update({"replica/" + r: _REP + r + "/habitat/mesh_semantic.ply" for r in REPLICA})   # 18 Replica scenes already on disk (74 GB), with navmeshes
AUX_DIRECTIONS = (-90.0, -45.0, 0.0, 45.0, 90.0)
BASE_KW = dict(rays=2048, bounces=4, ir_duration=0.3, threads=2, geodesic_range=(1.0, 8.0), max_steps=200, sounds=("telephone.wav",))
TASKS = {
    "audiogoal":      dict(goal_sound=True,  self_click=False, pointgoal=False, sliding=True),    # hear the goal, slide along walls (SoundSpaces)
    "blind_pointgoal": dict(goal_sound=False, self_click=False, pointgoal=True,  sliding=False),  # goal vector only; walls stop the agent
    "echo_pointgoal": dict(goal_sound=False, self_click=True,  pointgoal=True,  sliding=False),   # goal vector + self-click echoes
    "echo_audiogoal": dict(goal_sound=True,  self_click=True,  pointgoal=False, sliding=False),   # hear the goal + echoes
    "echo_scan_pointgoal": dict(goal_sound=False, self_click=True, pointgoal=True, sliding=False, scan_angles=(-45.0, 0.0, 45.0), click_dipole=(0.5, 2.0)),  # steerable click at 3 head angles
    # option 1: exploration in the dark (no goal); every agent gets a bump sensor
    "explore_blind":     dict(goal_sound=False, self_click=False, pointgoal=False, sliding=False, explore=True, contact=True, max_steps=300),
    "explore_echo":      dict(goal_sound=False, self_click=True,  pointgoal=False, sliding=False, explore=True, contact=True, max_steps=300),
    "explore_echo_scan": dict(goal_sound=False, self_click=True,  pointgoal=False, sliding=False, explore=True, contact=True, max_steps=300, scan_angles=(-45.0, 0.0, 45.0), click_dipole=(0.5, 2.0)),
    # option 2: sounding goal, walls stop the agent, with / without echoes
    "audiogoal_nosliding": dict(goal_sound=True, self_click=False, pointgoal=False, sliding=False, contact=True),
    "echo_audiogoal_nosliding": dict(goal_sound=True, self_click=True, pointgoal=False, sliding=False, contact=True),
}
# active sensing: sonar-image observation (range x azimuth from the ambisonic click response) and a policy-chosen click beam per step
# forward-only narrow beams: cardioid^8 = ((1 + cos)/2)^8 (half-power ~ +-30 deg, nothing behind). The BEAMS above use dipole weight 1,
# which Steam Audio evaluates as |cos|^4: a figure-eight that also fires backwards.
FWD = lambda name, yaw: (name, yaw, 0.5, 8.0)
BEAMS_FWD = (FWD("left90", 90.0), FWD("left45", 45.0), FWD("ahead", 0.0), FWD("right45", -45.0), FWD("right90", -90.0))
BEAMS = (("none", 0.0, 0.0, 1.0), ("omni", 0.0, 0.0, 1.0), ("left", 45.0, 1.0, 4.0), ("ahead", 0.0, 1.0, 4.0), ("right", -45.0, 1.0, 4.0))   # (name, yaw, dipole weight, power)
TASKS.update({
    "explore_sonar":      dict(goal_sound=False, self_click=True, pointgoal=False, sliding=False, explore=True, contact=True, max_steps=300, echo_obs="sonar"),           # fixed omni click, sonar image
    "explore_sonar_beam": dict(goal_sound=False, self_click=True, pointgoal=False, sliding=False, explore=True, contact=True, max_steps=300, echo_obs="sonar", beams=BEAMS, click_cost=0.01),
    # range-only sensor (no direction in the echo): direction comes only from where the click is aimed
    "explore_range_omni":  dict(goal_sound=False, self_click=True, pointgoal=False, sliding=False, explore=True, contact=True, max_steps=300, echo_obs="range"),
    "explore_range_ahead": dict(goal_sound=False, self_click=True, pointgoal=False, sliding=False, explore=True, contact=True, max_steps=300, echo_obs="range", beams=(FWD("ahead", 0.0),), beam_cycle=True),
    "explore_range_scan":  dict(goal_sound=False, self_click=True, pointgoal=False, sliding=False, explore=True, contact=True, max_steps=300, echo_obs="range", beams=BEAMS_FWD, beam_cycle=True),
    "explore_range_beam":  dict(goal_sound=False, self_click=True, pointgoal=False, sliding=False, explore=True, contact=True, max_steps=300, echo_obs="range", beams=(("none", 0.0, 0.0, 1.0),) + BEAMS_FWD, click_cost=0.01),
    "sonar_beam_pointgoal": dict(goal_sound=False, self_click=True, pointgoal=True, sliding=False, echo_obs="sonar", beams=BEAMS, click_cost=0.01),
})
ENV_KW = dict(BASE_KW, **TASKS["audiogoal"])
OBS_SHAPES = {"spectrogram": (2, 65, 26), "echo": (2, 65, 64), "sonar": (2, 64, 32), "range": (64,), "pointgoal": (2,), "contact": (1,)}   # defaults; overwritten from the first observation
VECTOR_KEYS = ("pointgoal", "contact", "range")

class AudioCNN(nn.Module):
    """SoundSpaces AudioCNN: 3 conv layers on the (2, 65, 26) spectrogram -> 512 features"""
    def __init__(self, shape=(2, 65, 26), out=512):
        super().__init__()
        self.conv = nn.Sequential(nn.Conv2d(shape[0], 32, (8, 4), (4, 2)), nn.ReLU(), nn.Conv2d(32, 64, (4, 3), (2, 2)), nn.ReLU(), nn.Conv2d(64, 32, (3, 3), 1), nn.ReLU(), nn.Flatten())
        with torch.no_grad(): n = self.conv(torch.zeros(1, *shape)).shape[1]
        self.fc = nn.Sequential(nn.Linear(n, out), nn.ReLU())
    def forward(self, x): return self.fc(self.conv(x))

class JointDist:
    """independent navigation and click-beam choices; actions are (..., 2) long tensors [nav, beam]"""
    def __init__(self, nav, beam): self.nav, self.beam = nav, beam
    def sample(self): return torch.stack([self.nav.sample(), self.beam.sample()], -1)
    def mode(self): return torch.stack([self.nav.probs.argmax(-1), self.beam.probs.argmax(-1)], -1)
    def log_prob(self, a): return self.nav.log_prob(a[..., 0]) + self.beam.log_prob(a[..., 1])
    def entropy(self): return self.nav.entropy() + self.beam.entropy()

def greedy(dist): return dist.mode() if isinstance(dist, JointDist) else dist.probs.argmax(-1)

class Policy(nn.Module):
    """multi-input: AudioCNN per image-like key ('spectrogram', 'echo', 'sonar'), MLP for 'pointgoal' (dist, bearing -> dist, cos, sin); GRU core.
    n_beams > 0 adds a second actor head choosing the click beam of the next step (JointDist) and an embedding of the previous beam."""
    def __init__(self, keys, n_actions=4, hidden=512, shapes=None, n_beams=0):
        super().__init__(); self.keys = list(keys); self.enc = nn.ModuleDict(); n_in = 32; shapes = shapes or OBS_SHAPES; self.n_beams = n_beams
        if n_beams: self.beam_emb = nn.Embedding(n_beams + 1, 16); n_in += 16
        for k in self.keys:
            if k == "pointgoal": self.enc[k] = nn.Sequential(nn.Linear(3, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU()); n_in += 32
            elif k == "contact": self.enc[k] = nn.Sequential(nn.Linear(1, 16), nn.ReLU()); n_in += 16
            elif k == "range": self.enc[k] = nn.Sequential(nn.Linear(shapes[k][0], 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU()); n_in += 256
            else: self.enc[k] = AudioCNN(shapes[k]); n_in += 512
        self.act_emb = nn.Embedding(n_actions + 1, 32); self.gru = nn.GRUCell(n_in, hidden)
        self.actor = nn.Linear(hidden, n_actions); self.critic = nn.Linear(hidden, 1); self.hidden = hidden
        if n_beams: self.beam_actor = nn.Linear(hidden, n_beams); nn.init.orthogonal_(self.beam_actor.weight, 0.01); nn.init.zeros_(self.beam_actor.bias)
        self.aux = nn.Sequential(nn.Linear(hidden, 128), nn.ReLU(), nn.Linear(128, len(AUX_DIRECTIONS)))   # predicts log1p(distance to nearest surface) per direction
        nn.init.orthogonal_(self.actor.weight, 0.01); nn.init.zeros_(self.actor.bias); nn.init.orthogonal_(self.critic.weight, 1.0); nn.init.zeros_(self.critic.bias)
    def features(self, obs):
        fs = []
        for k in self.keys:
            x = obs[k]
            if k == "pointgoal": x = torch.stack([x[..., 0] / 10.0, torch.cos(x[..., 1]), torch.sin(x[..., 1])], -1)
            fs.append(self.enc[k](x))
        return torch.cat(fs, -1)
    def _input(self, feats, prev_action, prev_beam):
        x = [feats, self.act_emb(prev_action)]
        if self.n_beams: x.append(self.beam_emb(prev_beam if prev_beam is not None else torch.full_like(prev_action, self.n_beams)))
        return torch.cat(x, -1)
    def _dist(self, h):
        nav = torch.distributions.Categorical(logits=self.actor(h))
        return JointDist(nav, torch.distributions.Categorical(logits=self.beam_actor(h))) if self.n_beams else nav
    def step(self, obs, prev_action, h, mask, prev_beam=None):
        """one time step for all envs: obs dict of (N,...) tensors, prev_action (N,) long, h (N,H), mask (N,) 1=continuing, prev_beam (N,) long or None"""
        h = self.gru(self._input(self.features(obs), prev_action, prev_beam), h * mask[:, None])
        return self._dist(h), self.critic(h).squeeze(-1), h
    def sequence(self, obs, prev_action, h0, masks, prev_beam=None):
        """obs dict of (T,N,...), prev_action (T,N), h0 (N,H), masks (T,N), prev_beam (T,N) or None -> action distribution over (T,N), values (T,N)"""
        T, N = prev_action.shape; feats = self.features({k: v.flatten(0, 1) for k, v in obs.items()}).view(T, N, -1)
        h = h0; values, hs = [], []
        for t in range(T):
            h = self.gru(self._input(feats[t], prev_action[t], None if prev_beam is None else prev_beam[t]), h * masks[t][:, None]); values.append(self.critic(h).squeeze(-1)); hs.append(h)
        self.last_hidden_seq = torch.stack(hs)
        return self._dist(self.last_hidden_seq), torch.stack(values)

def load_policy(ck, device):
    """build a Policy from a checkpoint; remaps state dicts saved by the single-input (spectrogram-only) version"""
    keys = ck.get("keys", ["spectrogram"]); policy = Policy(keys, shapes=ck.get("shapes"), n_beams=ck.get("n_beams", 0)).to(device)
    sd = ck["policy"]
    if any(k.startswith("enc.conv") or k.startswith("enc.fc") for k in sd): sd = {("enc.spectrogram." + k[4:] if k.startswith("enc.") else k): v for k, v in sd.items()}
    missing, unexpected = policy.load_state_dict(sd, strict=False)   # checkpoints trained before the aux head lack 'aux.*' (unused at test time)
    bad = [k for k in missing if not k.startswith("aux.")] + list(unexpected)
    if bad: raise RuntimeError(f"state dict mismatch: {bad}")
    policy.eval(); return policy, keys

def obs_keys(env_kw):
    keys = []
    if env_kw["goal_sound"]: keys.append("spectrogram")
    if env_kw["self_click"]: keys.append({"sonar": "sonar", "range": "range"}.get(env_kw.get("echo_obs"), "echo"))
    if env_kw["pointgoal"]: keys.append("pointgoal")
    if env_kw.get("contact"): keys.append("contact")
    return keys

def to_tensor(obs_list, device, keys):
    out = {}
    for k in keys:
        a = np.stack([o[k] for o in obs_list]); 
        if k not in VECTOR_KEYS: a = a.transpose(0, 3, 1, 2)
        out[k] = torch.as_tensor(a, dtype=torch.float32, device=device)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=600000); ap.add_argument("--envs", type=int, default=8); ap.add_argument("--rollout", type=int, default=128)
    ap.add_argument("--epochs", type=int, default=4); ap.add_argument("--minibatches", type=int, default=4); ap.add_argument("--lr", type=float, default=2.5e-4)
    ap.add_argument("--gamma", type=float, default=0.99); ap.add_argument("--lam", type=float, default=0.95); ap.add_argument("--clip", type=float, default=0.2)
    ap.add_argument("--entropy", type=float, default=0.02); ap.add_argument("--vf", type=float, default=0.5); ap.add_argument("--out", default="habitat_audio/runs/ppo_apartment1")
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--resume", default=None); ap.add_argument("--task", default="audiogoal", choices=list(TASKS)); ap.add_argument("--collision-penalty", type=float, default=0.0)
    ap.add_argument("--scenes", default="apartment_1", help="comma-separated scene names (see SCENES); worker i gets scene i mod n")
    ap.add_argument("--aux", type=float, default=0.0, help="weight of the auxiliary nearest-surface-distance prediction loss (0 = off)")
    ap.add_argument("--env-threads", type=int, default=2, help="Steam Audio threads per environment process")
    ap.add_argument("--rays", type=int, default=None); ap.add_argument("--bounces", type=int, default=None)
    ap.add_argument("--save-every", type=int, default=500000, help="also keep a checkpoint_<steps>.pt every this many steps")
    ap.add_argument("--echo-dropout", type=float, default=0.0, help="probability per step of blanking the echo/sonar observation (training augmentation)")
    ap.add_argument("--click-cost", type=float, default=None, help="override the task's per-click reward cost (beam tasks)")
    args = ap.parse_args(); os.makedirs(args.out, exist_ok=True); torch.manual_seed(args.seed); np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cpu_policy = device.type == "cpu"
    if cpu_policy: torch.set_num_threads(6); print("CUDA unavailable: policy on CPU with 6 threads (set OMP_WAIT_POLICY=PASSIVE so idle threads do not spin)", flush=True)
    env_kw = dict(BASE_KW, **TASKS[args.task]); env_kw["collision_penalty"] = args.collision_penalty; env_kw["threads"] = args.env_threads
    if args.rays: env_kw["rays"] = args.rays
    if args.bounces: env_kw["bounces"] = args.bounces
    if args.aux > 0: env_kw["aux_directions"] = AUX_DIRECTIONS
    if args.click_cost is not None: env_kw["click_cost"] = args.click_cost
    if args.echo_dropout > 0: env_kw["echo_dropout"] = args.echo_dropout
    scene_list = [SCENES[n.strip()] for n in args.scenes.split(",")]
    keys = obs_keys(env_kw); n_beams = len(env_kw["beams"]) if (env_kw.get("beams") and not env_kw.get("beam_cycle")) else 0
    print("task", args.task, "observation keys", keys, "beams", n_beams, flush=True)
    from habitat_audio.vec_env import SubprocVecEnv
    venv = SubprocVecEnv(scene_list, args.envs, env_kw, seed=args.seed * 100 + 1); print("scenes:", [os.path.basename(s) for s in venv.scenes], flush=True)
    N, T, H = args.envs, args.rollout, 512
    first = venv.reset(); shapes = {k: (tuple(np.transpose(first[0][k], (2, 0, 1)).shape) if k not in VECTOR_KEYS else tuple(first[0][k].shape)) for k in keys}; OBS_SHAPES.update(shapes)
    print("observation shapes", shapes, flush=True)
    policy = Policy(keys, shapes=shapes, n_beams=n_beams).to(device); opt = torch.optim.Adam(policy.parameters(), lr=args.lr, eps=1e-5)
    total = 0; update = 0
    if args.resume:
        ck = torch.load(args.resume, map_location=device); policy.load_state_dict(ck["policy"]); opt.load_state_dict(ck["opt"]); total = ck["steps"]; update = ck["update"]
    obs = to_tensor(first, device, keys); h = torch.zeros(N, H, device=device)
    aux_now = torch.as_tensor(np.stack(venv.last_aux), dtype=torch.float32, device=device) if args.aux > 0 else None; prev_a = torch.full((N,), 4, dtype=torch.long, device=device); mask = torch.ones(N, device=device)
    prev_b = torch.full((N,), n_beams, dtype=torch.long, device=device) if n_beams else None
    log = open(os.path.join(args.out, "log.csv"), "a"); 
    if log.tell() == 0: log.write("update,steps,time_s,episodes,success_rate,spl,return,length,policy_loss,value_loss,entropy,sps,collisions,coverage_cells,clicks\n")
    ep_stats = []; t_start = time.time(); n_updates = math.ceil(args.steps / (N * T))
    while total < args.steps:
        # ---------------- rollout
        S_obs = {k: torch.zeros(T, N, *OBS_SHAPES[k], device=device) for k in keys}; S_act = torch.zeros(T, N, 2, dtype=torch.long, device=device) if n_beams else torch.zeros(T, N, dtype=torch.long, device=device)
        S_prev = torch.zeros(T, N, dtype=torch.long, device=device); S_prevb = torch.zeros(T, N, dtype=torch.long, device=device) if n_beams else None
        S_logp = torch.zeros(T, N, device=device); S_val = torch.zeros(T + 1, N, device=device); S_rew = torch.zeros(T, N, device=device); S_mask = torch.zeros(T + 1, N, device=device)
        h0 = h.clone(); t_roll = time.time(); S_aux = torch.zeros(T, N, len(AUX_DIRECTIONS), device=device) if args.aux > 0 else None
        for t in range(T):
            with torch.no_grad(): dist, value, h = policy.step(obs, prev_a, h, mask, prev_b)
            a = dist.sample()
            for k in keys: S_obs[k][t] = obs[k]
            if args.aux > 0: S_aux[t] = aux_now
            S_act[t] = a; S_prev[t] = prev_a; S_logp[t] = dist.log_prob(a); S_val[t] = value; S_mask[t] = mask
            if n_beams: S_prevb[t] = prev_b
            obs_l, rew, done, infos = venv.step(a.cpu().numpy())
            for d, inf in zip(done, infos):
                if d: ep_stats.append((float(inf["success"]), inf["spl"], inf["step"], inf.get("collisions", 0), inf.get("coverage_cells", 0), inf.get("clicks", 0)))
            S_rew[t] = torch.as_tensor(rew, device=device); mask = torch.as_tensor(~done, dtype=torch.float32, device=device); done_t = torch.as_tensor(done, device=device)
            if args.aux > 0: aux_now = torch.as_tensor(np.stack([inf["aux_dist"] for inf in infos]), dtype=torch.float32, device=device)
            a_nav = a[:, 0] if n_beams else a
            prev_a = torch.where(done_t, torch.full_like(a_nav, 4), a_nav); obs = to_tensor(obs_l, device, keys); total += N
            if n_beams: prev_b = torch.where(done_t, torch.full_like(a_nav, n_beams), a[:, 1])
        with torch.no_grad(): _, S_val[T], _ = policy.step(obs, prev_a, h, mask, prev_b)
        S_mask[T] = mask
        # GAE (reward bookkeeping: an episode's return is summed inside the env; done resets value bootstrap via mask)
        adv = torch.zeros(T, N, device=device); last = torch.zeros(N, device=device)
        for t in reversed(range(T)):
            delta = S_rew[t] + args.gamma * S_val[t + 1] * S_mask[t + 1] - S_val[t]; last = delta + args.gamma * args.lam * S_mask[t + 1] * last; adv[t] = last
        ret = adv + S_val[:T]; adv_n = (adv - adv.mean()) / (adv.std() + 1e-8)
        # ---------------- PPO update (minibatches = subsets of environments, full sequences)
        pl_s, vl_s, ent_s, aux_s = [], [], [], []; env_idx = np.arange(N)
        for _ in range(args.epochs):
            np.random.shuffle(env_idx)
            for mb in np.array_split(env_idx, min(args.minibatches, N)):
                mb = torch.as_tensor(mb, device=device)
                dist, values = policy.sequence({k: v[:, mb] for k, v in S_obs.items()}, S_prev[:, mb], h0[mb], S_mask[:T, mb], None if S_prevb is None else S_prevb[:, mb])
                logp = dist.log_prob(S_act[:, mb]); ratio = torch.exp(logp - S_logp[:, mb])
                a_mb = adv_n[:, mb]; pl = -torch.min(ratio * a_mb, torch.clamp(ratio, 1 - args.clip, 1 + args.clip) * a_mb).mean()
                vl = 0.5 * F.mse_loss(values, ret[:, mb]); ent = dist.entropy().mean(); loss = pl + args.vf * vl - args.entropy * ent
                if args.aux > 0:
                    pred = policy.aux(policy.last_hidden_seq); target = torch.log1p(S_aux[:, mb]); al = F.mse_loss(pred, target); loss = loss + args.aux * al; aux_s.append(al.item())
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(policy.parameters(), 0.5); opt.step()
                pl_s.append(pl.item()); vl_s.append(vl.item()); ent_s.append(ent.item())
        update += 1; recent = ep_stats[-100:]
        sr = np.mean([e[0] for e in recent]) if recent else float("nan"); spl = np.mean([e[1] for e in recent]) if recent else float("nan"); ln = np.mean([e[2] for e in recent]) if recent else float("nan")
        rtn = S_rew.sum(0).mean().item(); col = np.mean([e[3] for e in recent]) if recent else float("nan"); cov = np.mean([e[4] for e in recent]) if recent else float("nan")
        clk = np.mean([e[5] for e in recent]) if recent else float("nan")
        sps = N * T / (time.time() - t_roll)
        log.write(f"{update},{total},{time.time()-t_start:.0f},{len(ep_stats)},{sr:.3f},{spl:.3f},{rtn:.3f},{ln:.1f},{np.mean(pl_s):.4f},{np.mean(vl_s):.4f},{np.mean(ent_s):.3f},{sps:.0f},{col:.1f},{cov:.1f},{clk:.1f}\n"); log.flush()
        print(f"update {update}/{n_updates} steps {total} episodes {len(ep_stats)} success(100) {sr:.2f} spl {spl:.2f} len {ln:.0f} collisions {col:.1f} coverage {cov:.1f} clicks {clk:.0f} rollout-reward {rtn:.2f} ent {np.mean(ent_s):.2f} aux {np.mean(aux_s) if aux_s else float('nan'):.3f} {sps:.0f} sps", flush=True)
        crossed = args.save_every > 0 and (total // args.save_every) > ((total - N * T) // args.save_every)
        if update % 10 == 0 or total >= args.steps or crossed:
            ck = {"policy": policy.state_dict(), "opt": opt.state_dict(), "steps": total, "update": update, "env_kw": env_kw, "keys": keys, "task": args.task, "shapes": shapes, "scenes": args.scenes, "aux": args.aux, "n_beams": n_beams}
            torch.save(ck, os.path.join(args.out, "checkpoint.pt"))
            if crossed: torch.save(ck, os.path.join(args.out, f"checkpoint_{(total // args.save_every) * args.save_every}.pt"))
    venv.close(); print("done")

if __name__ == "__main__": main()
