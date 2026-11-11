#!/bin/bash
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue2_results.md; D=$R/explore_echo_scan
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
until ! pgrep -f "ppo_eval --ckpt $D" >/dev/null; do sleep 30; done     # let the queue's (failing) ablation attempts finish first
echo -e "\n## explore: head-scan echo + bump sensor, 1M (re-evaluation after loader fix)" >> $OUT
nice python -m habitat_audio.ppo_eval --ckpt $D/checkpoint.pt --episodes 100 > $D/eval_full.log 2>&1; grep -E "^PPO|^random|^bump|Traceback" $D/eval_full.log | sed 's/^/    /' >> $OUT
for a in shuffled zeros; do nice python -m habitat_audio.ppo_eval --ckpt $D/checkpoint.pt --episodes 100 --ablate $a --skip-baselines > $D/eval_$a.log 2>&1; grep -E "^PPO|Traceback" $D/eval_$a.log | sed 's/^/    /' >> $OUT; done
