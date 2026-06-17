from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import threading
import time

COOKIES_PATH = os.path.join(os.path.dirname(__file__), 'cookies.txt')

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
    print("\n===== API HIT =====")

    try:
        data = request.json
        print("DATA:", data)

        url = data.get('url', '').strip()
        print("URL:", url)

        if not url:
            return jsonify({'error': 'URL required'}), 400

        ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'skip_download': True,
            'socket_timeout': 15,
        }

        if os.path.exists(COOKIES_PATH):
            ydl_opts['cookiefile'] = COOKIES_PATH

        print("Starting extraction...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        print("Extraction completed!")

        # Fix 1: Formats update kar diye taaki Frontend par options aayen
        formats = [
            {
                'format_id': 'bestvideo+bestaudio',
                'label': 'Video + Audio (Best Quality)',
                'filesize': None
            },
            {
                'format_id': 'audio',
                'label': 'Audio Only (MP3)',
                'filesize': None
            }
        ]

        return jsonify({
            'title': info.get('title', 'Unknown'),
            'thumbnail': info.get('thumbnail', ''),
            'duration': info.get('duration', 0),
            'uploader': info.get('uploader', 'Unknown'),
            'view_count': info.get('view_count', 0),
            'formats': formats
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({'error': str(e)}), 400


# Fix 2: POST ko GET me badal diya taaki browser RAM crash na ho
@app.route('/api/download', methods=['GET'])
def download():
    """Download video/audio"""
    # GET request ke parameters read karne ke liye request.args ka use
    url = request.args.get('url', '').strip()
    format_id = request.args.get('format_id', 'bestvideo+bestaudio')
    is_audio = format_id == 'audio'

    if not url:
        return jsonify({'error': 'URL required'}), 400

    output_path = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')

    if is_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'cookiefile': COOKIES_PATH,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        if os.path.exists(COOKIES_PATH):
            ydl_opts['cookiefile'] = COOKIES_PATH
    else:
        ydl_opts = {
            'format': f'{format_id}/best' if format_id != 'bestvideo+bestaudio' else 'bestvideo+bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'cookiefile': COOKIES_PATH,
            'merge_output_format': 'mp4',
        }
        if os.path.exists(COOKIES_PATH):
            ydl_opts['cookiefile'] = COOKIES_PATH

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

            # Fix 3: Delay badha kar 1 ghanta (3600 sec) kar diya
            cleanup_file(filename, delay=3600)

            return send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename)
            )

    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5000)