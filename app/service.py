import os
import tempfile
import librosa
import numpy as np
import requests
import yt_dlp

def fetch_external_bpm(artist: str, title: str) -> int | None:
    try:
        url = f"https://api.getsongbpm.com/search/?api_key=YOUR_API_KEY&type=both&lookup=song:{title} artist:{artist}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if "search" in data and len(data["search"]) > 0:
                return int(float(data["search"][0].get("tempo", 0)))
    except Exception as e:
        print(f"External API failed: {e}")
    return None

def analyze_librosa_bpm(youtube_video_id: str) -> int:
    video_url = f"https://www.youtube.com/watch?v={youtube_video_id}"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        wav_path = os.path.join(temp_dir, f"{youtube_video_id}.wav")
        if not os.path.exists(wav_path):
            raise FileNotFoundError("WAV file not created")
            
        y, sr = librosa.load(wav_path, sr=22050)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        bpm_val = float(tempo[0]) if isinstance(tempo, (np.ndarray, list)) else float(tempo)
        return int(round(bpm_val))

def process_music_bpm(youtube_video_id: str, title: str, artist: str) -> tuple[int, str]:
    external_bpm = fetch_external_bpm(artist, title)
    if external_bpm and external_bpm > 0:
        return external_bpm, "EXTERNAL_API"
        
    librosa_bpm = analyze_librosa_bpm(youtube_video_id)
    return librosa_bpm, "LIBROSA"