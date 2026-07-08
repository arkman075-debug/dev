import os
from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS

# This tells Flask exactly where the current folder is
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
CORS(app)

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        # This will print the exact error to the Render logs
        return str(e)

# ... keep the rest of your /get_info and /download routes here ...

if __name__ == '__main__':
    # Render uses an environment variable for PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# STEP 1: Route to get video details (Title, Thumbnail, Formats)
@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    ydl_opts = {'quiet': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Filter formats to show only useful ones (MP4 and MP3)
            formats = []
            for f in info.get('formats', []):
                # We only want formats that have a resolution (video) or are audio-only
                if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                    formats.append({
                        'format_id': f['format_id'],
                        'ext': f['ext'],
                        'resolution': f.get('resolution', 'Audio Only'),
                        'filesize': f.get('filesize', 0)
                    })

            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'formats': formats
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# STEP 2: Route to actually download the selected format
@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    video_url = data.get('url')
    format_id = data.get('format_id') # User's choice

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            # Ensure the extension is correct after merging
            if not os.path.exists(file_path):
                file_path = file_path.rsplit('.', 1)[0] + ".mp4"

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)