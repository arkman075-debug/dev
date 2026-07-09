import os
import yt_dlp
from flask import Flask, render_template, request, send_file, jsonify, after_this_request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        # Use yt-dlp to get info instead of the Google API
        ydl_opts = {'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        return jsonify({
            'title': info.get('title'),
            'thumbnail': info.get('thumbnail'),
            'channel': info.get('uploader'),
            'duration': info.get('duration_string')
        })

    except Exception as e:
        return jsonify({"error": f"Could not fetch video info: {str(e)}"}), 500

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "URL is required"}), 400

    # Using %(id)s avoids filename encoding errors
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(id)s.%(ext)s',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            # This is the name the user will see when saving
            safe_title = "".join([c for c in info['title'] if c.isalnum() or c in (' ', '.', '_')]).rstrip()
            download_name = f"{safe_title}.mp4"

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
            return response

        return send_file(
            file_path, 
            as_attachment=True, 
            download_name=download_name,
            mimetype='video/mp4'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
