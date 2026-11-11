"""Learning curves from runs/<name>/log.csv -> runs/<name>/learning_curves.png"""
import sys, os, numpy as np, csv
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
run = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/steamaudio/habitat_audio/runs/ppo_apartment1")
rows = list(csv.DictReader(open(os.path.join(run, "log.csv"))))
steps = np.array([float(r["steps"]) for r in rows]); f = lambda k: np.array([float(r[k]) for r in rows])
fig, axs = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
axs[0,0].plot(steps, f("success_rate")); axs[0,0].set_ylabel("success rate (last 100 episodes)"); axs[0,0].set_ylim(0, 1)
axs[0,1].plot(steps, f("spl")); axs[0,1].set_ylabel("SPL (last 100 episodes)"); axs[0,1].set_ylim(0, 1)
axs[1,0].plot(steps, f("length")); axs[1,0].set_ylabel("episode length (steps)")
axs[1,1].plot(steps, f("entropy"), label="policy entropy"); axs[1,1].plot(steps, f("return"), label="reward per env per rollout"); axs[1,1].legend()
for ax in axs.flat: ax.set_xlabel("environment steps"); ax.grid(alpha=0.3)
fig.suptitle("PPO audio-goal navigation on apartment_1 (Steam Audio acoustics)"); fig.savefig(os.path.join(run, "learning_curves.png"), dpi=120); print("saved")
