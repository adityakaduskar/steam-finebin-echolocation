#!/bin/bash
# Resume queue 5 after the pause of 2026-11-07 18:00: continue stage 2 (sonar, fixed omni click) from its checkpoint, then the rest.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue5_results.md; LOG=$R/queue5.log
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
sed -n '/^TRAIN=/,/^train() /p' habitat_audio/queue5.sh | grep -v '^echo "# Queue 5\|^source ' > /tmp/q5defs.$$ ; source /tmp/q5defs.$$; rm /tmp/q5defs.$$
resume() {  # resume <run_dir> [args]: like launch_train.sh but keeps the directory and continues from checkpoint.pt
  export OMP_WAIT_POLICY=PASSIVE OMP_NUM_THREADS=6 STEAMAUDIO_LIB=$HOME/steamaudio/sdk/lib/patched_embree/libphonon.so STEAMAUDIO_EMBREE=1
  setsid nohup python -m habitat_audio.ppo_train --out "$1" --resume "$1/checkpoint.pt" "${@:2}" >> "$1/train.log" 2>&1 < /dev/null &
  echo "resumed $1 pid $!" >> $LOG; wait_done "$1"
}
echo "# Queue 5 resumed $(date)" >> $OUT
COMMON="--scenes $TRAIN --collision-penalty 0.02 --steps 2000000 --envs 14 --env-threads 1 --rollout 128 --seed 1"
resume $R/q5_sonar_explore --task explore_sonar --aux 0.5 $COMMON && evaluate $R/q5_sonar_explore "Replica explore: sonar image, fixed omni click + aux, penalty 0.02, 2M" 30
train $R/q5_blind_explore --task explore_blind $COMMON && evaluate $R/q5_blind_explore "Replica explore: blind, penalty 0.02, 2M" 30
train $R/q5_echo_scan_explore --task explore_echo_scan --aux 0.5 $COMMON && evaluate $R/q5_echo_scan_explore "Replica explore: head-scan binaural spectrogram + aux, penalty 0.02, 2M" 30
echo -e "\n# Queue 5 finished $(date)" >> $OUT; touch $R/queue5_done.flag
