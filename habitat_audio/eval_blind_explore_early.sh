#!/bin/bash
R=~/steamaudio/habitat_audio/runs; D=$R/q3_blind_explore; OUT=$R/queue3_results.md
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
until grep -q "^done" $D/train.log 2>/dev/null; do sleep 60; done
echo -e "\n## explore: blind, 3 scenes, 2M (early evaluation while the head-scan explorer trains)" >> $OUT
for sc in apartment_1 van-gogh-room skokloster-castle 17DRP5sb8fy; do
  echo "### scene $sc $([ $sc = 17DRP5sb8fy ] && echo '(HELD OUT)' || echo '(train)')" >> $OUT
  nice python -m habitat_audio.ppo_eval --ckpt $D/checkpoint.pt --episodes 30 --scene $sc > $D/eval_$sc.log 2>&1
  grep -E "^PPO|^random|^bump" $D/eval_$sc.log | sed 's/^/    /' >> $OUT; grep -q Traceback $D/eval_$sc.log && echo "    EVAL FAILED" >> $OUT
done
