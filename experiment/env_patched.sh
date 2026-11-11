# source this file to run wall_experiment / run_scenarios.py against the patched core in sample-accurate sparse mode
export LD_LIBRARY_PATH=$HOME/steamaudio/sdk/lib/patched
export STEAMAUDIO_BIN_DURATION=2.0833333e-5     # 1/48000 s -> one energy-histogram bin per sample
export STEAMAUDIO_RECONSTRUCTION=sparse          # deterministic impulses instead of noise
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6   # conda python ships an older libstdc++; the rebuilt core needs GLIBCXX_3.4.30
# Embree tracer (same physics, faster): uncomment
# export LD_LIBRARY_PATH=$HOME/steamaudio/sdk/lib/patched_embree; export STEAMAUDIO_LIB=$HOME/steamaudio/sdk/lib/patched_embree/libphonon.so STEAMAUDIO_EMBREE=1
