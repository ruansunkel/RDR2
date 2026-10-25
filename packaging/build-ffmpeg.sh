#!/bin/bash
# Build only the FFmpeg demuxing libraries used by Wine's winedmo; no global install.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/vendor/ffmpeg-source/ffmpeg-9.0.2"
BUILD="$ROOT/vendor/ffmpeg-build-x86_64"
OUT="$ROOT/vendor/ffmpeg-install-x86_64"
[[ -f "$SRC/configure" ]] || { echo 'Fetch and safely extract the pinned FFmpeg source first.' >&2; exit 1; }
export CLANG_MODULE_CACHE_PATH="$ROOT/.cache/clang"
mkdir -p "$BUILD" "$OUT"
cd "$BUILD"
"$SRC/configure" --prefix="$OUT" --install-name-dir=@rpath \
    --arch=x86_64 --target-os=darwin --enable-cross-compile --cc=clang --cxx=clang++ \
    --extra-cflags='-arch x86_64 -mmacosx-version-min=14.0' \
    --extra-ldflags='-arch x86_64 -mmacosx-version-min=14.0' \
    --enable-shared --disable-static --disable-autodetect --disable-everything \
    --disable-programs --disable-doc --disable-avdevice --disable-avfilter \
    --disable-swresample --disable-swscale --disable-network --disable-x86asm \
    --enable-avformat --enable-avcodec --enable-avutil --enable-demuxers \
    --enable-parsers --enable-bsf=null --enable-protocol=file,pipe
/usr/bin/make -j4
/usr/bin/make install
cp "$SRC/COPYING.LGPLv2.1" "$SRC/LICENSE.md" "$OUT/"
cp ffbuild/config.mak config.h "$OUT/"
echo "Built demuxing runtime at $OUT. Full decoding remains provided by GStreamer."
