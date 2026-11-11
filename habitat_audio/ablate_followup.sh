#!/bin/bash
# Companion to queue.sh: for each echo run, once its evaluation block exists in queue_results.md, run the shuffled/zeroed echo ablations.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue_results.md
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
for r in ppo_echo_scan_cp ppo_echo_cp_1p5M ppo_echo_scan_cp_1p5M ppo_echo_cp_seed2 ppo_echo_scan_cp_seed2; do
  until grep -q "($R/$r," $OUT 2>/dev/null && [ -f $R/$r/eval_100.json ]; do if [ -f $R/queue_done.flag ] && ! grep -q "($R/$r," $OUT; then break; fi; sleep 60; done
  grep -q "($R/$r," $OUT || continue
  echo -e "\n## ablation of $r" >> $OUT
  for a in shuffled zeros; do python -m habitat_audio.ppo_eval --ckpt $R/$r/checkpoint.pt --episodes 100 --ablate $a --skip-baselines 2>&1 | grep -E "^PPO|Traceback" | sed 's/^/    /' >> $OUT; done
done
touch $R/ablate_done.flag
