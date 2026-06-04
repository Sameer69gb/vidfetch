#!/usr/bin/env bash
# Exit on error
set -o errexit

# Python requirements install karo
pip install -r requirements.txt

# FFmpeg download aur setup karo (Kyunki Render mein root access nahi hota)
echo "Downloading FFmpeg..."
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
mkdir -p bin
cp ffmpeg-*-amd64-static/ffmpeg bin/
cp ffmpeg-*-amd64-static/ffprobe bin/
rm -rf ffmpeg-*-amd64-static*
echo "FFmpeg installed successfully!"