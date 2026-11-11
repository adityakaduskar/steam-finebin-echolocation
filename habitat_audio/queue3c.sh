#!/bin/bash
# Queue 3c: continuation after the reboot. Waits for the resumed head-scan explorer, evaluates it, then runs stage 3.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue3_results.md; LOG=$R/queue3.log; TRAIN=apartment_1,van-gogh-room,skokloster-castle
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
echo -e "\n# Queue 3c resumed $(date) after reboot (GPU back)" >> $OUT
wait_done() { until grep -q "^done" "$1/train.log" 2>/dev/null; do if grep -q Traceback "$1/train.log" 2>/dev/null; then echo "CRASH in $1" >> $OUT; return 1; fi; sleep 60; done; }
has_echo() { python -c "import torch,sys; sys.exit(0 if 'echo' in torch.load('$1/checkpoint.pt',map_location='cpu')['keys'] else 1)" 2>/dev/null; }
evaluate() {  # evaluate <run_dir> <label> <episodes>
  python habitat_audio/plot_training.py $1 >/dev/null 2>&1
  echo -e "\n## $2  ($1, $(grep '^update' $1/train.log | tail -1 | cut -d' ' -f2-6))" >> $OUT
  for sc in apartment_1 van-gogh-room skokloster-castle 17DRP5sb8fy; do
    echo "### scene $sc $([ $sc = 17DRP5sb8fy ] && echo '(HELD OUT)' || echo '(train)')" >> $OUT
    for try in 1 2; do python -m habitat_audio.ppo_eval --ckpt $1/checkpoint.pt --episodes $3 --scene $sc > $1/eval_$sc.log 2>&1 && break; sleep 30; done
    grep -E "^PPO|^random|^oracle|^bump" $1/eval_$sc.log | sed 's/^/    /' >> $OUT; grep -q Traceback $1/eval_$sc.log && echo "    EVAL FAILED" >> $OUT
  done
  if has_echo $1; then for a in shuffled zeros; do
    for try in 1 2; do python -m habitat_audio.ppo_eval --ckpt $1/checkpoint.pt --episodes $3 --scene 17DRP5sb8fy --ablate $a --skip-baselines > $1/eval_heldout_$a.log 2>&1 && break; sleep 30; done
    echo "### held-out scene, echoes $a" >> $OUT; grep -E "^PPO" $1/eval_heldout_$a.log | sed 's/^/    /' >> $OUT
  done; fi
}
train() { bash habitat_audio/launch_train.sh "$1" "${@:2}" >> $LOG 2>&1; wait_done "$1"; }
wait_done $R/q3_echo_scan_explore_aux && evaluate $R/q3_echo_scan_explore_aux "explore: head-scan echo + aux loss, 3 scenes, 2M (resumed after reboot)" 30
train $R/q3_echo_pointgoal_aux --task echo_pointgoal --scenes $TRAIN --aux 0.5 --collision-penalty 0.1 --steps 2000000 --envs 8 --rollout 128 --seed 1 && evaluate $R/q3_echo_pointgoal_aux "point-goal: single-pose echo + aux loss, 3 scenes, 2M" 100
echo -e "\n# Queue 3 finished $(date)" >> $OUT; touch $R/queue3_done.flag
