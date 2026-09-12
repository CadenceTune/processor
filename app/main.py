from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.collector import PlaylistCollector
from app.analyzer import BpmAnalyzer

app = FastAPI()
collector = PlaylistCollector()
analyzer = BpmAnalyzer()

class PlaylistRequest(BaseModel):
    playlist_url: str

class BpmRequest(BaseModel):
    title: str
    artist: str = ""
    youtube_url: str = None

@app.post("/api/processor/playlist")
def get_playlist(request: PlaylistRequest):
    try:
        tracks = collector.fetch_playlist_tracks(request.playlist_url)
        # Spring Boot ProcessorClient 규격에 맞춰 status와 tracks로 감싸서 반환
        return {
            "status": "success",
            "tracks": tracks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/processor/bpm")
def get_bpm(request: BpmRequest):
    try:
        bpm = analyzer.get_bpm(request.title, request.artist, request.youtube_url)
        return {
            "status": "success",
            "bpm": bpm
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))