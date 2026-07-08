import os
import yt_dlp
from flask import Flask, render_template, request, send_file, jsonify
from googleapiclient.discovery import build
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 1. Define the folder where videos will be saved
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# 2. Get the API Key from Render environment variables
# In Render, set a variable named YOUTUBE_API_KEY and paste your key there
API_KEY = os.environ.get('')

if not API_KEY:
    print("WARNING: YOUTUBE_API_KEY environment variable is not set!")
    youtube = None
else:
    youtube = build('youtube', 'v3', developerKey=API_KEY)

# Helper function to get the Video ID from a URL
def get_video_id(url):
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'be/' in url:
        return url.split('be/')[1].split('?')[0]
    return None

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
            'channel': video_data['channelTitle']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    video_url = data.get('url')
    format_id = data.get('format_id')

    if not video_url:
        return jsonify({"error": "URL is required"}), 400

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Use environment port for Render, default to 5000 for local
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
