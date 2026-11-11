#!/bin/bash
# Option 1 (exploration in the dark) then option 2 (sounding goal + echoes, walls stop the agent). Sequential; results -> runs/queue2_results.md
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue2_results.md; LOG=$R/queue2.log
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
echo "# Queue 2 started $(date)" >> $OUT
wait_done() { until grep -q "^done" "$1/train.log" 2>/dev/null; do if grep -q Traceback "$1/train.log" 2>/dev/null; then echo "CRASH in $1" >> $OUT; return 1; fi; sleep 60; done; }
has_echo() { python -c "import torch,sys; sys.exit(0 if 'echo' in torch.load('$1/checkpoint.pt',map_location='cpu')['keys'] else 1)" 2>/dev/null; }
evaluate() {  # evaluate <run_dir> <label>
  python habitat_audio/plot_training.py $1 >/dev/null 2>&1
  echo -e "\n## $2  ($1, $(grep '^update' $1/train.log | tail -1 | cut -d' ' -f2-6))" >> $OUT
  for try in 1 2; do python -m habitat_audio.ppo_eval --ckpt $1/checkpoint.pt --episodes 100 > $1/eval_full.log 2>&1 && break; sleep 30; done
  grep -E "^PPO|^random|^oracle|^bump" $1/eval_full.log | sed 's/^/    /' >> $OUT; grep -q Traceback $1/eval_full.log && echo "    EVAL FAILED (see eval_full.log)" >> $OUT
  if has_echo $1; then for a in shuffled zeros; do
    for try in 1 2; do python -m habitat_audio.ppo_eval --ckpt $1/checkpoint.pt --episodes 100 --ablate $a --skip-baselines > $1/eval_$a.log 2>&1 && break; sleep 30; done
    grep -E "^PPO" $1/eval_$a.log | sed 's/^/    /' >> $OUT; grep -q Traceback $1/eval_$a.log && echo "    ABLATION $a FAILED" >> $OUT
  done; fi
}
train() { bash habitat_audio/launch_train.sh "$1" "${@:2}" >> $LOG 2>&1; wait_done "$1"; }
# ---- option 1: exploration in the dark, 1M steps each; blind in parallel with echo (no acoustics)
bash habitat_audio/launch_train.sh $R/explore_blind --task explore_blind --collision-penalty 0.1 --steps 1000000 --envs 4 --rollout 128 --seed 1 >> $LOG 2>&1
train $R/explore_echo --task explore_echo --collision-penalty 0.1 --steps 1000000 --envs 8 --rollout 128 --seed 1 && evaluate $R/explore_echo "explore: single-pose echo + bump sensor, 1M"
wait_done $R/explore_blind && evaluate $R/explore_blind "explore: blind (bump sensor only), 1M"
train $R/explore_echo_scan --task explore_echo_scan --collision-penalty 0.1 --steps 1000000 --envs 8 --rollout 128 --seed 1 && evaluate $R/explore_echo_scan "explore: head-scan echo + bump sensor, 1M"
# ---- option 2: sounding goal, walls stop the agent, with / without echoes, 1M steps each
train $R/audiogoal_nosliding --task audiogoal_nosliding --collision-penalty 0.1 --steps 1000000 --envs 8 --rollout 128 --seed 1 && evaluate $R/audiogoal_nosliding "audio-goal, no sliding, no echoes, 1M"
train $R/echo_audiogoal_nosliding --task echo_audiogoal_nosliding --collision-penalty 0.1 --steps 1000000 --envs 8 --rollout 128 --seed 1 && evaluate $R/echo_audiogoal_nosliding "audio-goal, no sliding, + echoes, 1M"
echo -e "\n# Queue 2 finished $(date)" >> $OUT; touch $R/queue2_done.flag
