from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.music_processor_service import MusicProcessorService

router = APIRouter(prefix="/api/processor", tags=["processor"])
music_processor_service = MusicProcessorService()

class PlaylistRequest(BaseModel):
    playlist_url: str  # Java에서 보내는 requestBody 키 "playlist_url"과 일치

@router.post("/playlist")
def get_playlist_tracks(request: PlaylistRequest):
    try:
        tracks = music_processor_service.fetch_playlist_tracks(request.playlist_url)
        return {
            "status": "success",
            "tracks": tracks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))