#!/bin/bash
# Queue 5: active sensing on Replica (14 training scenes, same held-out set as queue 4). Exploration in the dark, collision penalty 0.02.
#  1. sonar image + policy-chosen click beam (none/omni/left/ahead/right, click cost 0.01)   2. sonar image, fixed omni click
#  3. blind (penalty control)   4. head-scan binaural spectrogram explorer (queue 4 sensor, penalty control)
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue5_results.md; LOG=$R/queue5.log
TRAIN=replica/apartment_0,replica/apartment_1,replica/apartment_2,replica/frl_apartment_0,replica/frl_apartment_1,replica/frl_apartment_2,replica/frl_apartment_3,replica/frl_apartment_5,replica/office_0,replica/office_1,replica/office_3,replica/office_4,replica/room_0,replica/room_1
HELD="replica/office_2 replica/frl_apartment_4 replica/hotel_0 replica/room_2"; TRAINEVAL="replica/apartment_0 replica/office_0 replica/room_0"
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
echo "# Queue 5 (Replica, active sensing, exploration, collision penalty 0.02) started $(date)" >> $OUT
wait_done() { until grep -q "^done" "$1/train.log" 2>/dev/null; do if grep -q Traceback "$1/train.log" 2>/dev/null; then echo "CRASH in $1" >> $OUT; return 1; fi; sleep 60; done; }
has_echo() { python -c "import torch,sys; k=torch.load('$1/checkpoint.pt',map_location='cpu')['keys']; sys.exit(0 if ('echo' in k or 'sonar' in k) else 1)" 2>/dev/null; }
ev() { for try in 1 2; do python -m habitat_audio.ppo_eval --ckpt $1 --episodes $2 --scene $3 $4 > $5.log 2>&1 && break; sleep 30; done; grep -E "^PPO|^random|^oracle|^bump" $5.log | sed 's/^/    /' >> $OUT; grep -q Traceback $5.log && echo "    EVAL FAILED" >> $OUT; }
evaluate() {  # evaluate <run_dir> <label> <episodes>
  python habitat_audio/plot_training.py $1 >/dev/null 2>&1
  echo -e "\n## $2  ($1, $(grep '^update' $1/train.log | tail -1 | cut -d' ' -f2-6))" >> $OUT
  for sc in $HELD; do echo "### $sc (HELD OUT)" >> $OUT; ev $1/checkpoint.pt $3 $sc "" $1/eval_$(basename $sc); done
  for sc in $TRAINEVAL; do echo "### $sc (train)" >> $OUT; ev $1/checkpoint.pt $3 $sc "" $1/eval_$(basename $sc); done
  if has_echo $1; then
    for a in shuffled zeros; do echo "### held-out office_2 + hotel_0, echoes $a" >> $OUT; for sc in replica/office_2 replica/hotel_0; do ev $1/checkpoint.pt $3 $sc "--ablate $a --skip-baselines" $1/eval_$(basename $sc)_$a; done; done
    for ck in $1/checkpoint_500000.pt $1/checkpoint_1000000.pt $1/checkpoint_1500000.pt; do [ -f $ck ] || continue; echo "### interim $(basename $ck) on held-out office_2 + hotel_0" >> $OUT; for sc in replica/office_2 replica/hotel_0; do ev $ck $3 $sc "--skip-baselines" $1/eval_$(basename $sc)_$(basename $ck .pt); done; done
  fi
}
train() { bash habitat_audio/launch_train.sh "$1" "${@:2}" >> $LOG 2>&1; wait_done "$1"; }
COMMON="--scenes $TRAIN --collision-penalty 0.02 --steps 2000000 --envs 14 --env-threads 1 --rollout 128 --seed 1"
train $R/q5_sonar_beam_explore --task explore_sonar_beam --aux 0.5 $COMMON && evaluate $R/q5_sonar_beam_explore "Replica explore: sonar image + learned click beam (cost 0.01) + aux, penalty 0.02, 2M" 30
train $R/q5_sonar_explore --task explore_sonar --aux 0.5 $COMMON && evaluate $R/q5_sonar_explore "Replica explore: sonar image, fixed omni click + aux, penalty 0.02, 2M" 30
train $R/q5_blind_explore --task explore_blind $COMMON && evaluate $R/q5_blind_explore "Replica explore: blind, penalty 0.02, 2M" 30
train $R/q5_echo_scan_explore --task explore_echo_scan --aux 0.5 $COMMON && evaluate $R/q5_echo_scan_explore "Replica explore: head-scan binaural spectrogram + aux, penalty 0.02, 2M" 30
echo -e "\n# Queue 5 finished $(date)" >> $OUT; touch $R/queue5_done.flag
