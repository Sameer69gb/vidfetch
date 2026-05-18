from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import threading
import time

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = tempfile.mkdtemp()

def cleanup_file(filepath, delay=60):
    """Delete file after delay seconds"""
    def _delete():
        time.sleep(delay)
        if os.path.exists(filepath):
            os.remove(filepath)
    threading.Thread(target=_delete, daemon=True).start()


@app.route('/api/info', methods=['POST'])
def get_info():
    """Get video info without downloading"""
    data = request.json
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL required'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'cookiefile': 'cookies.txt',
        'extractor_args': {'facebook': {'api': ['next']}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            seen = set()
            
            for f in info.get('formats', []):
                height = f.get('height')
                ext = f.get('ext')
                vcodec = f.get('vcodec', 'none')
                
                if height and vcodec != 'none' and ext in ['mp4', 'webm']:
                    label = f"{height}p ({ext})"
                    if label not in seen:
                        seen.add(label)
                        formats.append({
                            'format_id': f['format_id'],
                            'label': label,
                            'height': height,
                            'ext': ext,
                            'filesize': f.get('filesize') or f.get('filesize_approx')
                        })

            formats.sort(key=lambda x: x['height'], reverse=True)
            
            formats.append({
                'format_id': 'audio',
                'label': 'MP3 (Audio Only)',
                'height': 0,
                'ext': 'mp3',
                'filesize': None
            })

            return jsonify({
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'formats': formats
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/download', methods=['POST'])
def download():
    """Download video/audio"""
    data = request.json
    url = data.get('url', '').strip()
    format_id = data.get('format_id', 'bestvideo+bestaudio')
    is_audio = format_id == 'audio'

    if not url:
        return jsonify({'error': 'URL required'}), 400

    output_path = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')

    if is_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        ydl_opts = {
            'format': f'{format_id}+bestaudio/{format_id}/best',
            'outtmpl': output_path,
            'quiet': True,
            'merge_output_format': 'mp4',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if is_audio:
                base = os.path.splitext(filename)[0]
                filename = base + '.mp3'

            if not os.path.exists(filename):
                title = info.get('title', '')
                for f in os.listdir(DOWNLOAD_DIR):
                    if title[:20] in f:
                        filename = os.path.join(DOWNLOAD_DIR, f)
                        break

            cleanup_file(filename, delay=120)

            return send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename)
            )

    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5000)