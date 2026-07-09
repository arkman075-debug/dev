import os
import yt_dlp
import shutil
from flask import Flask, render_template, request, send_file, jsonify, after_this_request
from googleapiclient.discovery import build
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Get the API Key from Render environment variables
API_KEY = os.environ.get('YOUTUBE_API_KEY')

if not API_KEY:
    print("WARNING: YOUTUBE_API_KEY environment variable is not set!")
    youtube = None
else:
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
    except Exception as e:
        print(f"FAILED to initialize YouTube API: {e}")
        youtube = None

# --- HELPERS ---
def get_video_id(url):
    """Extracts the video ID from various YouTube URL formats."""
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'be/' in url:
        return url.split('be/')[1].split('?')[0]
    elif 'shorts/' in url:
        return url.split('shorts/')[1].split('?')[0]
    return None

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    if youtube is None:
        return jsonify({"error": "YouTube API is not configured on the server"}), 500
    
    data = request.json
    url = data.get('url')
    video_id = get_video_id(url)

    if not video_id:
        return jsonify({"error": "Could not find video ID in the URL"}), 400
    
    try:
        request_api = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request_api.execute()

        if not response['items']:
            return jsonify({"error": "Video not found on YouTube"}), 404

        video_data = response['items'][0]['snippet']
        
        return jsonify({
            'title': video_data['title'],
            'thumbnail': video_data['thumbnails']['high']['url'],
            'channel': video_data['channelTitle'],
            'video_id': video_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "URL is required"}), 400

    # We use video ID as the filename to avoid character encoding issues
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(id)s.%(ext)s',
        'noplaylist': True,
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            download_name = f"{info.get('title', 'video')}.mp4"

        # This ensures the file is deleted from the Render server AFTER it is sent to the user
        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Error deleting file: {e}")
            return response

        return send_file(
            file_path, 
            as_attachment=True, 
            download_name=download_name,
            mimetype='video/mp4'
        )

    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
