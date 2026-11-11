#!/bin/bash
# Download the stock Steam Audio 4.8.1 SDK (headers, docs, stock libphonon.so) into sdk/ and sdk/lib/stock/.
set -euo pipefail; cd "$(dirname "$0")/.."
mkdir -p downloads/sdk sdk/lib/stock
[ -f downloads/sdk/steamaudio_4.8.1.zip ] || curl -L -o downloads/sdk/steamaudio_4.8.1.zip \
  https://github.com/ValveSoftware/steam-audio/releases/download/v4.8.1/steamaudio_4.8.1.zip
unzip -qo downloads/sdk/steamaudio_4.8.1.zip -d downloads/sdk
cp -r downloads/sdk/steamaudio/include downloads/sdk/steamaudio/doc sdk/ 2>/dev/null || true
cp downloads/sdk/steamaudio/lib/linux-x64/libphonon.so sdk/lib/stock/
echo "stock SDK in sdk/ (lib: sdk/lib/stock/libphonon.so)"
