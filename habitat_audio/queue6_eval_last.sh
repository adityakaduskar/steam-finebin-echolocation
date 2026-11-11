#!/bin/bash
# Queue 6: Replica exploration, collision penalty 0.05, three seeds per agent; echo agents trained with 5% blank-echo augmentation.
# Order: sonar fixed click, sonar + learned beam, blind (all fast), then head-scan binaural (8 h each) last.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue6_results.md; LOG=$R/queue6.log
TRAIN=replica/apartment_0,replica/apartment_1,replica/apartment_2,replica/frl_apartment_0,replica/frl_apartment_1,replica/frl_apartment_2,replica/frl_apartment_3,replica/frl_apartment_5,replica/office_0,replica/office_1,replica/office_3,replica/office_4,replica/room_0,replica/room_1
HELD="replica/office_2 replica/frl_apartment_4 replica/hotel_0 replica/room_2"
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
echo "# Queue 6 resumed for the last evaluation $(date)" >> $OUT
wait_done() { until grep -q "^done" "$1/train.log" 2>/dev/null; do if grep -q Traceback "$1/train.log" 2>/dev/null; then echo "CRASH in $1" >> $OUT; return 1; fi; sleep 60; done; }
gpu_free() { while ps -eo args | grep -E "[h]abitat_audio.ppo_(train|eval)" | grep -vq spawn; do sleep 60; done; }
ev() { for try in 1 2; do python -m habitat_audio.ppo_eval --ckpt $1 --episodes $2 --scene $3 $4 > $5.log 2>&1 && break; sleep 30; done; grep -E "^PPO|^bump" $5.log | sed 's/^/    /' >> $OUT; grep -q Traceback $5.log && echo "    EVAL FAILED" >> $OUT; }
evaluate() {  # evaluate <run_dir> <label> <seed> <echo 0/1>
  python habitat_audio/plot_training.py $1 >/dev/null 2>&1
  echo -e "\n## $2, seed $3  ($(grep '^update' $1/train.log | tail -1 | cut -d' ' -f2-6))" >> $OUT
  base=""; [ "$3" != 1 ] && base="--skip-baselines"   # heuristic baseline once (seed 1)
  for sc in $HELD; do echo "### $sc (HELD OUT)" >> $OUT; ev $1/checkpoint.pt 30 $sc "$base" $1/eval_$(basename $sc); done
  if [ "$4" = 1 ]; then for a in shuffled zeros; do echo "### office_2 + hotel_0, echoes $a" >> $OUT; for sc in replica/office_2 replica/hotel_0; do ev $1/checkpoint.pt 30 $sc "--ablate $a --skip-baselines" $1/eval_$(basename $sc)_$a; done; done; fi
  python habitat_audio/summarize_seeds.py > $R/queue6_summary.md 2>&1
}
train() { gpu_free; bash habitat_audio/launch_train.sh "$1" "${@:2}" >> $LOG 2>&1; wait_done "$1"; }
gpu_free; evaluate $R/q6_echo_scan_s3 "head-scan binaural" 3 1
echo -e "\n# Queue 6 finished $(date)\n" >> $OUT; cat $R/queue6_summary.md >> $OUT; touch $R/queue6_done.flag
