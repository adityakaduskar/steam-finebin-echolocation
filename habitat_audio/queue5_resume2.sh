#!/bin/bash
# Queue 5 continuation (2026-11-07 22:40): the sonar/omni run (pid 301103, resumed from its checkpoint) is still training; wait for it
# ignoring the tracebacks left in its log by the pause, evaluate it, then run the two controls.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue5_results.md; LOG=$R/queue5.log
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
sed -n '/^TRAIN=/,/^train() /p' habitat_audio/queue5.sh | grep -v '^echo "# Queue 5\|^source ' > /tmp/q5defs.$$ ; source /tmp/q5defs.$$; rm /tmp/q5defs.$$
SKIP=4074   # log lines written before this continuation (contain the pause tracebacks)
wait_resumed() { until grep -q "^done" "$1/train.log" 2>/dev/null; do if tail -n +$SKIP "$1/train.log" | grep -q Traceback; then echo "CRASH in $1" >> $OUT; return 1; fi; sleep 60; done; }
COMMON="--scenes $TRAIN --collision-penalty 0.02 --steps 2000000 --envs 14 --env-threads 1 --rollout 128 --seed 1"
wait_resumed $R/q5_sonar_explore && evaluate $R/q5_sonar_explore "Replica explore: sonar image, fixed omni click + aux, penalty 0.02, 2M" 30
train $R/q5_blind_explore --task explore_blind $COMMON && evaluate $R/q5_blind_explore "Replica explore: blind, penalty 0.02, 2M" 30
train $R/q5_echo_scan_explore --task explore_echo_scan --aux 0.5 $COMMON && evaluate $R/q5_echo_scan_explore "Replica explore: head-scan binaural spectrogram + aux, penalty 0.02, 2M" 30
echo -e "\n# Queue 5 finished $(date)" >> $OUT; touch $R/queue5_done.flag
