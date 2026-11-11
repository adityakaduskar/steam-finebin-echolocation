#!/bin/bash
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue2_results.md; D=$R/audiogoal_nosliding
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
echo -e "\n## audio-goal, no sliding, no echoes, 1M (re-evaluation after lib-path fix)" >> $OUT
nice python -m habitat_audio.ppo_eval --ckpt $D/checkpoint.pt --episodes 100 > $D/eval_full.log 2>&1; grep -E "^PPO|^random|^oracle|Traceback" $D/eval_full.log | sed 's/^/    /' >> $OUT
