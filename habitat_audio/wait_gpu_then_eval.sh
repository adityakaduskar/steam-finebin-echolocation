#!/bin/bash
# Start the last queue 6 evaluation only once the GPU has had no compute processes (and no PPO/echo-engine training)
# for 10 consecutive minutes, so a gap between another job's precompute and its training is not mistaken for free.
LOG=~/steamaudio/habitat_audio/runs/queue6_eval_last.out
busy() { [ -n "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null)" ] || ps -eo args | grep -qE "^[^ ]*python[^ ]* .*(train_echo_ppo|ppo_train|ppo_eval)"; }
echo "$(date) waiting for an idle GPU" >> $LOG; idle=0
while [ $idle -lt 10 ]; do if busy; then idle=0; else idle=$((idle+1)); fi; sleep 60; done
echo "$(date) GPU idle for 10 min, starting evaluation" >> $LOG
exec bash ~/steamaudio/habitat_audio/queue6_eval_last.sh >> $LOG 2>&1
