#!/bin/bash
# detached PPO training launcher: bash habitat_audio/launch_train.sh <out_dir> [extra args]
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss
# Embree-enabled core (validated identical to the default tracer; ~1.9x faster for head-scan tasks)
export OMP_WAIT_POLICY=PASSIVE OMP_NUM_THREADS=6
export STEAMAUDIO_LIB=$HOME/steamaudio/sdk/lib/patched_embree/libphonon.so STEAMAUDIO_EMBREE=1
cd ~/steamaudio && OUT=$1; shift; rm -rf "$OUT"; mkdir -p "$OUT"
setsid nohup python -m habitat_audio.ppo_train --out "$OUT" "$@" > "$OUT/train.log" 2>&1 < /dev/null &
echo "launched pid $!"
