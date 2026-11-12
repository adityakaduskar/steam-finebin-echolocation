#!/bin/bash
# Queue 10 (evaluation only): are collisions repeats at the same place? (paper marker J24). Runs after queue 9.
R=~/steamaudio/habitat_audio/runs; OUT=$R/queue10_results.md
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
export STEAMAUDIO_LIB=$HOME/steamaudio/sdk/lib/patched_embree/libphonon.so STEAMAUDIO_EMBREE=1
until [ -f $R/queue9_done.flag ]; do sleep 120; done
busy() { [ -n "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null)" ] || ps -eo args | grep -qE "^[^ ]*python[^ ]* .*(train_echo_ppo|ppo_train|ppo_eval|probe_map)"; }
i=0; while [ $i -lt 3 ]; do if busy; then i=0; else i=$((i+1)); fi; sleep 60; done
echo "# Queue 10 (collision repeats, memory intact vs erased every step) started $(date)" >> $OUT
for a in q6_sonar q6_sonar_beam q7_range_beam q6_blind; do for s in 1 2 3; do for n in 0 1; do for sc in office_2 hotel_0; do
  f=$R/${a}_s$s/coll${n}_$sc
  python -m habitat_audio.ppo_eval --ckpt $R/${a}_s$s/checkpoint.pt --episodes 30 --scene replica/$sc --reset-every $n --greedy-only --skip-baselines --log-collisions $f.json > $f.log 2>&1
  python -m habitat_audio.collision_repeats $f.json | sed "s|$R/||" >> $OUT
done; done; done; done
echo "# Queue 10 finished $(date)" >> $OUT; touch $R/queue10_done.flag
