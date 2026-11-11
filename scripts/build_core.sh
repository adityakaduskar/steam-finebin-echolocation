#!/bin/bash
# Build the patched Steam Audio 4.8.1 core (sample-resolution energy bins, sparse reconstruction, Embree bin fix, upstream fixes)
# into sdk/lib/patched/ and sdk/lib/patched_embree/. Needs git, cmake >= 3.17, a C++17 compiler, python3.
# Reconstructed from the CMake caches of the original builds; the original build was done step by step, not with this script.
set -euo pipefail; ROOT="$(cd "$(dirname "$0")/.." && pwd)"; SRC=$ROOT/core_src/steam-audio
[ -d "$SRC" ] || git clone --branch v4.8.1 --depth 1 https://github.com/ValveSoftware/steam-audio.git "$SRC"
cd "$SRC"; git apply --check "$ROOT/patches/steam-audio-4.8.1-echolocation.patch" 2>/dev/null && git apply "$ROOT/patches/steam-audio-4.8.1-echolocation.patch" || echo "patch already applied?"
cd core/build && python3 get_dependencies.py --platform linux && python3 get_dependencies.py --platform linux --dependency embree || true
common="-DCMAKE_BUILD_TYPE=Release -DSTEAMAUDIO_BUILD_TESTS=FALSE -DSTEAMAUDIO_BUILD_BENCHMARKS=FALSE -DSTEAMAUDIO_BUILD_SAMPLES=FALSE \
 -DSTEAMAUDIO_BUILD_DOCS=FALSE -DSTEAMAUDIO_BUILD_ITESTS=FALSE -DSTEAMAUDIO_ENABLE_IPP=FALSE -DSTEAMAUDIO_ENABLE_MKL=OFF -DSTEAMAUDIO_ENABLE_AVX=ON \
 -DSTEAMAUDIO_ENABLE_RADEONRAYS=FALSE -DSTEAMAUDIO_ENABLE_TRUEAUDIONEXT=FALSE -DSTEAMAUDIO_STATIC_RUNTIME=ON"
for v in release:FALSE:patched embree:TRUE:patched_embree; do IFS=: read name emb out <<< "$v"
  cmake -S .. -B linux-x64-$name $common -DSTEAMAUDIO_ENABLE_EMBREE=$emb && cmake --build linux-x64-$name -j"$(nproc)"
  mkdir -p "$ROOT/sdk/lib/$out"; cp "$(find linux-x64-$name -name libphonon.so | head -1)" "$ROOT/sdk/lib/$out/"; done
echo "built: sdk/lib/patched/libphonon.so and sdk/lib/patched_embree/libphonon.so"
