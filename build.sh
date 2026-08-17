#!/usr/bin/env bash
set -o errexit

# Python requirements install 
pip install -r requirements.txt

# FFmpeg download aur setup
echo "Downloading FFmpeg..."

wget -O ffmpeg.tar.xz \
  https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-linux64-gpl.tar.xz

tar -xf ffmpeg.tar.xz

mkdir -p bin

cp ffmpeg-master-latest-linux64-gpl/bin/ffmpeg bin/
cp ffmpeg-master-latest-linux64-gpl/bin/ffprobe bin/

rm -rf ffmpeg-master-latest-linux64-gpl ffmpeg.tar.xz

echo "FFmpeg installed successfully!"