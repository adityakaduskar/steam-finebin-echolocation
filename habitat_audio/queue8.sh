#!/bin/bash
# Queue 8 (2026-11-11): A) memory wipe -- evaluate trained explorers with their GRU memory reset every 20 steps / every step;
# B) click-cost sweep for the range + learned-beam explorer (cost 0, 0.03, 0.1; 0.01 = queue 7), 3 seeds each.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue8_results.md; LOG=$R/queue8.log
TRAIN=replica/apartment_0,replica/apartment_1,replica/apartment_2,replica/frl_apartment_0,replica/frl_apartment_1,replica/frl_apartment_2,replica/frl_apartment_3,replica/frl_apartment_5,replica/office_0,replica/office_1,replica/office_3,replica/office_4,replica/room_0,replica/room_1
HELD="replica/office_2 replica/frl_apartment_4 replica/hotel_0 replica/room_2"
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
export STEAMAUDIO_LIB=$HOME/steamaudio/sdk/lib/patched_embree/libphonon.so STEAMAUDIO_EMBREE=1
echo "# Queue 8 (memory wipe + click-cost sweep) started $(date)" >> $OUT
busy() { [ -n "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null)" ] || ps -eo args | grep -qE "^[^ ]*python[^ ]* .*(train_echo_ppo|ppo_train|ppo_eval|probe_map)"; }
gpu_idle() { local i=0; while [ $i -lt 3 ]; do if busy; then i=0; else i=$((i+1)); fi; sleep 60; done; }
wait_done() { until grep -q "^done" "$1/train.log" 2>/dev/null; do if grep -q Traceback "$1/train.log" 2>/dev/null; then echo "CRASH in $1" >> $OUT; return 1; fi; sleep 60; done; }
ev() { for try in 1 2; do python -m habitat_audio.ppo_eval --ckpt $1 --episodes $2 --scene $3 $4 > $5.log 2>&1 && break; sleep 30; done; grep -E "^PPO|^bump" $5.log | sed 's/^/    /' >> $OUT; grep -q Traceback $5.log && echo "    EVAL FAILED $5" >> $OUT; }
evaluate() {
  python habitat_audio/plot_training.py $1 >/dev/null 2>&1
  echo -e "\n## $2, seed $3  ($(grep '^update' $1/train.log | tail -1 | cut -d' ' -f2-6))" >> $OUT
  base=""; [ "$3" != 1 ] && base="--skip-baselines"
  for sc in $HELD; do echo "### $sc (HELD OUT)" >> $OUT; ev $1/checkpoint.pt 30 $sc "$base" $1/eval_$(basename $sc); done
  echo "### office_2 + hotel_0, echoes zeros" >> $OUT; for sc in replica/office_2 replica/hotel_0; do ev $1/checkpoint.pt 30 $sc "--ablate zeros --skip-baselines" $1/eval_$(basename $sc)_zeros; done
  python habitat_audio/summarize_q8.py > $R/queue8_summary.md 2>&1
}
train() { gpu_idle; bash habitat_audio/launch_train.sh "$1" "${@:2}" >> $LOG 2>&1; wait_done "$1"; }
# ---------------- A: memory wipe
echo -e "\n## A. memory wipe" >> $OUT; gpu_idle
for a in q6_blind q6_sonar q6_sonar_beam q7_range_beam; do for s in 1 2 3; do for n in 0 20 1; do
  echo "### ${a}_s$s, reset every $n" >> $OUT
  for sc in office_2 hotel_0; do ev $R/${a}_s$s/checkpoint.pt 30 replica/$sc "--reset-every $n --greedy-only --skip-baselines" $R/${a}_s$s/wipe${n}_$sc; done
done; done; done
python habitat_audio/summarize_q8.py > $R/queue8_summary.md 2>&1
# ---------------- B: click-cost sweep
echo -e "\n## B. click-cost sweep" >> $OUT
COMMON="--task explore_range_beam --scenes $TRAIN --collision-penalty 0.05 --steps 2000000 --envs 14 --env-threads 1 --rollout 128 --aux 0.5 --echo-dropout 0.05"
for c in "c0:0" "c003:0.03" "c01:0.1"; do IFS=: read tag cost <<< "$c"
  for s in 1 2 3; do train $R/q8_range_beam_${tag}_s$s $COMMON --click-cost $cost --seed $s && evaluate $R/q8_range_beam_${tag}_s$s "range + learned beam, click cost $cost" $s; done
done
echo -e "\n# Queue 8 finished $(date)\n" >> $OUT; cat $R/queue8_summary.md >> $OUT; touch $R/queue8_done.flag
