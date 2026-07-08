import os
from flask import Flask, jsonify
from googleapiclient.discovery import build

app = Flask(__name__)

# 1. Get the key
API_KEY = os.environ.get('AIzaSyA2USsNtl7uUl520HnVlgovSVMA48HyboA')

# 2. Add a check to prevent the crash you saw
if not API_KEY:
    print("WARNING: YOUTUBE_API_KEY is not set in environment variables!")
    youtube = None
else:
    # Use developerKey specifically to avoid the "Default Credentials" error
    youtube = build('youtube', 'v3', developerKey=API_KEY)

@app.route('/get_info', methods=['POST'])
def get_info():
    if youtube is None:
        return jsonify({"error": "API Key is missing on the server"}), 500
    
    # ... rest of your code ...
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
