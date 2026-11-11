#!/bin/bash
# Queue 7 (2026-11-10): A) map-building probe on the 12 queue 6 explorers; B) range-only echo sensor where direction comes only
# from where the click is aimed: learned beam vs scripted scan vs fixed ahead vs omni, 3 seeds each, Replica explore, penalty 0.05.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue7_results.md; LOG=$R/queue7.log; P=$R/probe
TRAIN=replica/apartment_0,replica/apartment_1,replica/apartment_2,replica/frl_apartment_0,replica/frl_apartment_1,replica/frl_apartment_2,replica/frl_apartment_3,replica/frl_apartment_5,replica/office_0,replica/office_1,replica/office_3,replica/office_4,replica/room_0,replica/room_1
HELD="replica/office_2 replica/frl_apartment_4 replica/hotel_0 replica/room_2"
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
export STEAMAUDIO_LIB=$HOME/steamaudio/sdk/lib/patched_embree/libphonon.so STEAMAUDIO_EMBREE=1
echo "# Queue 7 (map probe + range-only beam sensor) started $(date)" >> $OUT
# GPU guard: wait until no GPU compute process and no training/eval of either project has been seen for 3 minutes
busy() { [ -n "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null)" ] || ps -eo args | grep -qE "^[^ ]*python[^ ]* .*(train_echo_ppo|ppo_train|ppo_eval|probe_map)"; }
gpu_idle() { local i=0; while [ $i -lt 3 ]; do if busy; then i=0; else i=$((i+1)); fi; sleep 60; done; }
wait_done() { until grep -q "^done" "$1/train.log" 2>/dev/null; do if grep -q Traceback "$1/train.log" 2>/dev/null; then echo "CRASH in $1" >> $OUT; return 1; fi; sleep 60; done; }
ev() { for try in 1 2; do python -m habitat_audio.ppo_eval --ckpt $1 --episodes $2 --scene $3 $4 > $5.log 2>&1 && break; sleep 30; done; grep -E "^PPO|^bump" $5.log | sed 's/^/    /' >> $OUT; grep -q Traceback $5.log && echo "    EVAL FAILED" >> $OUT; }
AGENTS7="q7_range_beam:range + learned beam,q7_range_scan:range + scripted scan,q7_range_ahead:range + fixed ahead beam,q7_range_omni:range + omni click,q6_sonar:sonar image (queue 6 reference),q6_blind:blind (queue 6 reference)"
evaluate() {  # evaluate <run_dir> <label> <seed>
  python habitat_audio/plot_training.py $1 >/dev/null 2>&1
  echo -e "\n## $2, seed $3  ($(grep '^update' $1/train.log | tail -1 | cut -d' ' -f2-6))" >> $OUT
  base=""; [ "$3" != 1 ] && base="--skip-baselines"
  for sc in $HELD; do echo "### $sc (HELD OUT)" >> $OUT; ev $1/checkpoint.pt 30 $sc "$base" $1/eval_$(basename $sc); done
  for a in shuffled zeros; do echo "### office_2 + hotel_0, echoes $a" >> $OUT; for sc in replica/office_2 replica/hotel_0; do ev $1/checkpoint.pt 30 $sc "--ablate $a --skip-baselines" $1/eval_$(basename $sc)_$a; done; done
  python habitat_audio/summarize_seeds.py "$AGENTS7" > $R/queue7_summary.md 2>&1
}
train() { gpu_idle; bash habitat_audio/launch_train.sh "$1" "${@:2}" >> $LOG 2>&1; wait_done "$1"; }
# ---------------- A: map probe (policy on CPU; Habitat still opens a small GL context)
mkdir -p $P; echo -e "\n## A. map-building probe" >> $OUT
for a in q6_sonar q6_sonar_beam q6_blind q6_echo_scan; do for s in 1 2 3; do
  [ -f $P/${a}_s$s.npz ] || { gpu_idle; OMP_NUM_THREADS=4 python -m habitat_audio.probe_map collect --ckpt $R/${a}_s$s/checkpoint.pt --out $P/${a}_s$s.npz > $P/${a}_s$s.collect.log 2>&1; }
  OMP_NUM_THREADS=8 python -m habitat_audio.probe_map fit --data $P/${a}_s$s.npz > $P/${a}_s$s.fit.log 2>&1
  grep -E "AUROC" $P/${a}_s$s.fit.log | sed 's/^/    /' >> $OUT; grep -q Traceback $P/${a}_s$s.collect.log $P/${a}_s$s.fit.log && echo "    PROBE FAILED ${a}_s$s" >> $OUT
done; done
python -m habitat_audio.probe_map summary > /dev/null 2>&1; cat $P/probe_summary.md >> $OUT
# ---------------- B: range-only sensor
echo -e "\n## B. range-only echo sensor" >> $OUT
COMMON="--scenes $TRAIN --collision-penalty 0.05 --steps 2000000 --envs 14 --env-threads 1 --rollout 128 --aux 0.5 --echo-dropout 0.05"
for cfg in "range_beam:explore_range_beam:range + learned beam" "range_scan:explore_range_scan:range + scripted scan" "range_ahead:explore_range_ahead:range + fixed ahead beam" "range_omni:explore_range_omni:range + omni click"; do
  IFS=: read name task label <<< "$cfg"
  for s in 1 2 3; do train $R/q7_${name}_s$s --task $task --seed $s $COMMON && evaluate $R/q7_${name}_s$s "$label" $s; done
done
echo -e "\n# Queue 7 finished $(date)\n" >> $OUT; cat $R/queue7_summary.md >> $OUT; touch $R/queue7_done.flag
