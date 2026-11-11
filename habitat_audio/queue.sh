#!/bin/bash
# Unattended experiment queue. Each stage: train (detached launcher, wait for 'done'), evaluate on 100 held-out episodes (+ echo ablation),
# append to runs/queue_results.md. Stages run strictly one after another so they do not compete for CPU.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue_results.md; LOG=$R/queue.log
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
echo "# Queue started $(date)" >> $OUT
wait_done() { until grep -q "^done" "$1/train.log" 2>/dev/null; do if grep -q Traceback "$1/train.log" 2>/dev/null; then echo "CRASH in $1" >> $OUT; return 1; fi; sleep 60; done; }
evaluate() {  # evaluate <run_dir> <label>
  python habitat_audio/plot_training.py $1 >/dev/null 2>&1
  echo -e "\n## $2  ($1, $(grep '^update' $1/train.log | tail -1 | cut -d' ' -f2-6))" >> $OUT
  python -m habitat_audio.ppo_eval --ckpt $1/checkpoint.pt --episodes 100 2>&1 | grep -E "^PPO|^random|^oracle|Traceback" | sed 's/^/    /' >> $OUT
  if grep -q '"echo"' <(python -c "import torch;print(torch.load('$1/checkpoint.pt',map_location='cpu')['keys'])" 2>/dev/null); then
    python -m habitat_audio.ppo_eval --ckpt $1/checkpoint.pt --episodes 100 --ablate shuffled --skip-baselines 2>&1 | grep -E "^PPO|Traceback" | sed 's/^/    /' >> $OUT
    python -m habitat_audio.ppo_eval --ckpt $1/checkpoint.pt --episodes 100 --ablate zeros --skip-baselines 2>&1 | grep -E "^PPO|Traceback" | sed 's/^/    /' >> $OUT
  fi
}
train() {  # train <run_dir> <args...>
  bash habitat_audio/launch_train.sh "$1" "${@:2}" >> $LOG 2>&1; wait_done "$1"
}
# stage 0: the collision-penalty runs already in progress -> wait for their evaluation, add the echo ablation
until [ -f $R/penalty_done.flag ]; do sleep 60; done
for r in ppo_echo_pointgoal ppo_echo_pointgoal_cp; do
  echo -e "\n## ablation of $r" >> $OUT
  python -m habitat_audio.ppo_eval --ckpt $R/$r/checkpoint.pt --episodes 100 --skip-baselines 2>&1 | grep -E "^PPO" | sed 's/^/    /' >> $OUT
  python -m habitat_audio.ppo_eval --ckpt $R/$r/checkpoint.pt --episodes 100 --ablate shuffled --skip-baselines 2>&1 | grep -E "^PPO|Traceback" | sed 's/^/    /' >> $OUT
  python -m habitat_audio.ppo_eval --ckpt $R/$r/checkpoint.pt --episodes 100 --ablate zeros --skip-baselines 2>&1 | grep -E "^PPO|Traceback" | sed 's/^/    /' >> $OUT
done
echo -e "\n## penalty runs (600k, seed 1)" >> $OUT; for r in ppo_echo_pointgoal_cp ppo_blind_pointgoal_cp; do echo "### $r" >> $OUT; sed 's/^/    /' $R/$r/eval_summary.txt >> $OUT; done
# stage 1: head-scan echolocation, penalty, 600k
train $R/ppo_echo_scan_cp --task echo_scan_pointgoal --collision-penalty 0.1 --steps 600000 --envs 8 --rollout 128 --seed 1 && evaluate $R/ppo_echo_scan_cp "head-scan echo + penalty, 600k, seed 1"
# stage 2: longer training, 1.5M steps (blind in parallel with echo: it uses no acoustics)
bash habitat_audio/launch_train.sh $R/ppo_blind_cp_1p5M --task blind_pointgoal --collision-penalty 0.1 --steps 1500000 --envs 4 --rollout 128 --seed 1 >> $LOG 2>&1
train $R/ppo_echo_cp_1p5M --task echo_pointgoal --collision-penalty 0.1 --steps 1500000 --envs 8 --rollout 128 --seed 1 && evaluate $R/ppo_echo_cp_1p5M "single-pose echo + penalty, 1.5M, seed 1"
wait_done $R/ppo_blind_cp_1p5M && evaluate $R/ppo_blind_cp_1p5M "blind + penalty, 1.5M, seed 1"
# stage 3: head-scan echolocation, 1.5M
train $R/ppo_echo_scan_cp_1p5M --task echo_scan_pointgoal --collision-penalty 0.1 --steps 1500000 --envs 8 --rollout 128 --seed 1 && evaluate $R/ppo_echo_scan_cp_1p5M "head-scan echo + penalty, 1.5M, seed 1"
# stage 4: second seeds of the 600k penalty pair for variance
bash habitat_audio/launch_train.sh $R/ppo_blind_cp_seed2 --task blind_pointgoal --collision-penalty 0.1 --steps 600000 --envs 4 --rollout 128 --seed 2 >> $LOG 2>&1
train $R/ppo_echo_cp_seed2 --task echo_pointgoal --collision-penalty 0.1 --steps 600000 --envs 8 --rollout 128 --seed 2 && evaluate $R/ppo_echo_cp_seed2 "single-pose echo + penalty, 600k, seed 2"
wait_done $R/ppo_blind_cp_seed2 && evaluate $R/ppo_blind_cp_seed2 "blind + penalty, 600k, seed 2"
train $R/ppo_echo_scan_cp_seed2 --task echo_scan_pointgoal --collision-penalty 0.1 --steps 600000 --envs 8 --rollout 128 --seed 2 && evaluate $R/ppo_echo_scan_cp_seed2 "head-scan echo + penalty, 600k, seed 2"
echo -e "\n# Queue finished $(date)" >> $OUT; touch $R/queue_done.flag
