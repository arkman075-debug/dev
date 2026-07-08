import os
from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Securely get the API Key from Render's environment
API_KEY = os.environ.get('AIzaSyA2USsNtl7uUl520HnVlgovSVMA48HyboA')
youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_video_id(url):
    # Simple helper to extract the ID from a YouTube URL
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'be/' in url:
        return url.split('be/')[1].split('?')[0]
    return None

@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    video_id = get_video_id(url)

    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    try:
        # Call the official YouTube API
        request_api = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request_api.execute()

        if not response['items']:
            return jsonify({"error": "Video not found"}), 404

        video_data = response['items'][0]['snippet']
        
        return jsonify({
            'title': video_data['title'],
            'thumbnail': video_data['thumbnails']['high']['url'],
            'channel': video_data['channelTitle']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Note: The /download route using yt-dlp will still likely 
# face the "Sign in" block on Render's servers.
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
