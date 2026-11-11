"""Multiprocess vectorised SteamAudioNavEnv (spawn start method: each worker owns a Habitat GL context and a Steam Audio context)."""
import multiprocessing as mp
import numpy as np

def _worker(remote, scene, kwargs):
    import os, sys; sys.path.insert(0, os.path.expanduser("~/steamaudio"))
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"): os.environ[k] = "1"   # one BLAS thread per worker; Steam Audio threads are set separately
    from habitat_audio import SteamAudioNavEnv
    env = SteamAudioNavEnv(scene, **kwargs)
    try:
        while True:
            cmd, data = remote.recv()
            if cmd == "step":
                obs, r, done, info = env.step(data)
                if done:
                    info["final_obs"] = obs; obs = env.reset()
                remote.send((obs, r, done, info))
            elif cmd == "reset": obs = env.reset(**(data or {})); remote.send((obs, env.last_aux))
            elif cmd == "oracle": remote.send(env.oracle_action())
            elif cmd == "sample_episode": remote.send(env.sample_episode())
            elif cmd == "close": break
    finally:
        env.close(); remote.close()

class SubprocVecEnv:
    def __init__(self, scene, n, env_kwargs, seed=0):
        """scene: one path or a list of paths; worker i uses scene[i % len]"""
        scenes = scene if isinstance(scene, (list, tuple)) else [scene]
        ctx = mp.get_context("spawn"); self.remotes, self.procs = [], []
        for i in range(n):
            a, b = ctx.Pipe(); kw = dict(env_kwargs); kw["seed"] = seed + i
            p = ctx.Process(target=_worker, args=(b, scenes[i % len(scenes)], kw), daemon=True); p.start(); self.remotes.append(a); self.procs.append(p)
        self.n = n; self.scenes = [scenes[i % len(scenes)] for i in range(n)]
    def reset(self):
        for r in self.remotes: r.send(("reset", None))
        res = [r.recv() for r in self.remotes]; self.last_aux = [x[1] for x in res]; return [x[0] for x in res]
    def step(self, actions):
        for r, a in zip(self.remotes, actions): r.send(("step", int(a) if np.ndim(a) == 0 else tuple(int(x) for x in a)))
        res = [r.recv() for r in self.remotes]; obs, rew, done, info = zip(*res)
        return list(obs), np.array(rew, np.float32), np.array(done, bool), list(info)
    def close(self):
        for r in self.remotes: r.send(("close", None))
        for p in self.procs: p.join(timeout=10)
