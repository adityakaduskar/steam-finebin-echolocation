#!/bin/bash
# Queue 4: Replica. 14 training scenes (one environment process each), 4 held out (office_2, frl_apartment_4, hotel_0, room_2).
# Head-scan echo + aux loss vs blind; point-goal in the dark, then exploration. Checkpoints every 500k are evaluated on the held-out scenes.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue4_results.md; LOG=$R/queue4.log
TRAIN=replica/apartment_0,replica/apartment_1,replica/apartment_2,replica/frl_apartment_0,replica/frl_apartment_1,replica/frl_apartment_2,replica/frl_apartment_3,replica/frl_apartment_5,replica/office_0,replica/office_1,replica/office_3,replica/office_4,replica/room_0,replica/room_1
HELD="replica/office_2 replica/frl_apartment_4 replica/hotel_0 replica/room_2"; TRAINEVAL="replica/apartment_0 replica/office_0 replica/room_0"
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
echo "# Queue 4 (Replica) started $(date)" >> $OUT
wait_done() { until grep -q "^done" "$1/train.log" 2>/dev/null; do if grep -q Traceback "$1/train.log" 2>/dev/null; then echo "CRASH in $1" >> $OUT; return 1; fi; sleep 60; done; }
has_echo() { python -c "import torch,sys; sys.exit(0 if 'echo' in torch.load('$1/checkpoint.pt',map_location='cpu')['keys'] else 1)" 2>/dev/null; }
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
# stage 1: point-goal in the dark (sequential: 14 workers each)
train $R/q4_echo_scan_pointgoal_aux --task echo_scan_pointgoal --scenes $TRAIN --aux 0.5 --collision-penalty 0.1 --steps 2000000 --envs 14 --env-threads 1 --rollout 128 --seed 1 && evaluate $R/q4_echo_scan_pointgoal_aux "Replica point-goal: head-scan echo + aux, 14 scenes, 2M" 100
train $R/q4_blind_pointgoal --task blind_pointgoal --scenes $TRAIN --collision-penalty 0.1 --steps 2000000 --envs 14 --env-threads 1 --rollout 128 --seed 1 && evaluate $R/q4_blind_pointgoal "Replica point-goal: blind, 14 scenes, 2M" 100
# stage 2: exploration
train $R/q4_echo_scan_explore_aux --task explore_echo_scan --scenes $TRAIN --aux 0.5 --collision-penalty 0.1 --steps 2000000 --envs 14 --env-threads 1 --rollout 128 --seed 1 && evaluate $R/q4_echo_scan_explore_aux "Replica explore: head-scan echo + aux, 14 scenes, 2M" 30
train $R/q4_blind_explore --task explore_blind --scenes $TRAIN --collision-penalty 0.1 --steps 2000000 --envs 14 --env-threads 1 --rollout 128 --seed 1 && evaluate $R/q4_blind_explore "Replica explore: blind, 14 scenes, 2M" 30
echo -e "\n# Queue 4 finished $(date)" >> $OUT; touch $R/queue4_done.flag
