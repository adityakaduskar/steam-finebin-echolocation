#!/bin/bash
# Queue 9: controls for two confounds named in the paper: (a) blind agents trained WITH the auxiliary wall-distance loss;
# (b) sonar + learned beam with forward-only beams. Waits for queue 8 to finish.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue9_results.md; LOG=$R/queue9.log; P=$R/probe
TRAIN=replica/apartment_0,replica/apartment_1,replica/apartment_2,replica/frl_apartment_0,replica/frl_apartment_1,replica/frl_apartment_2,replica/frl_apartment_3,replica/frl_apartment_5,replica/office_0,replica/office_1,replica/office_3,replica/office_4,replica/room_0,replica/room_1
HELD="replica/office_2 replica/frl_apartment_4 replica/hotel_0 replica/room_2"
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
export STEAMAUDIO_LIB=$HOME/steamaudio/sdk/lib/patched_embree/libphonon.so STEAMAUDIO_EMBREE=1
until [ -f $R/queue8_done.flag ]; do sleep 120; done
echo "# Queue 9 (controls for paper confounds) started $(date)" >> $OUT
# GPU guard: wait until no GPU compute process and no training/eval of either project has been seen for 3 minutes
busy() { [ -n "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null)" ] || ps -eo args | grep -qE "^[^ ]*python[^ ]* .*(train_echo_ppo|ppo_train|ppo_eval|probe_map)"; }
gpu_idle() { local i=0; while [ $i -lt 3 ]; do if busy; then i=0; else i=$((i+1)); fi; sleep 60; done; }
wait_done() { until grep -q "^done" "$1/train.log" 2>/dev/null; do if grep -q Traceback "$1/train.log" 2>/dev/null; then echo "CRASH in $1" >> $OUT; return 1; fi; sleep 60; done; }
ev() { for try in 1 2; do python -m habitat_audio.ppo_eval --ckpt $1 --episodes $2 --scene $3 $4 > $5.log 2>&1 && break; sleep 30; done; grep -E "^PPO|^bump" $5.log | sed 's/^/    /' >> $OUT; grep -q Traceback $5.log && echo "    EVAL FAILED" >> $OUT; }
AGENTS9="q9_blind_aux:blind + auxiliary loss,q6_blind:blind without auxiliary loss (Exp. 1),q9_sonar_beam_fwd:sonar + learned forward beams,q6_sonar_beam:sonar + learned figure-of-eight beams (Exp. 1),q6_sonar:sonar fixed click (Exp. 1)"
evaluate() {  # evaluate <run_dir> <label> <seed> <echo 0/1>
  python habitat_audio/plot_training.py $1 >/dev/null 2>&1
  echo -e "\n## $2, seed $3  ($(grep '^update' $1/train.log | tail -1 | cut -d' ' -f2-6))" >> $OUT
  for sc in $HELD; do echo "### $sc (HELD OUT)" >> $OUT; ev $1/checkpoint.pt 30 $sc "--skip-baselines" $1/eval_$(basename $sc); done
  if [ "$4" = 1 ]; then for a in shuffled zeros; do echo "### office_2 + hotel_0, echoes $a" >> $OUT; for sc in replica/office_2 replica/hotel_0; do ev $1/checkpoint.pt 30 $sc "--ablate $a --skip-baselines" $1/eval_$(basename $sc)_$a; done; done; fi
  python habitat_audio/summarize_seeds.py "$AGENTS9" > $R/queue9_summary.md 2>&1
}
train() { gpu_idle; bash habitat_audio/launch_train.sh "$1" "${@:2}" >> $LOG 2>&1; wait_done "$1"; }
COMMON="--scenes $TRAIN --collision-penalty 0.05 --steps 2000000 --envs 14 --env-threads 1 --rollout 128 --aux 0.5"
for s in 1 2 3; do train $R/q9_blind_aux_s$s --task explore_blind --seed $s $COMMON && evaluate $R/q9_blind_aux_s$s "blind + auxiliary loss" $s 0; done
for s in 1 2 3; do train $R/q9_sonar_beam_fwd_s$s --task explore_sonar_beam_fwd --echo-dropout 0.05 --seed $s $COMMON && evaluate $R/q9_sonar_beam_fwd_s$s "sonar + learned forward beams" $s 1; done
echo -e "\n# Queue 9 finished $(date)\n" >> $OUT; cat $R/queue9_summary.md >> $OUT; touch $R/queue9_done.flag
