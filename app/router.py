from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.service import process_music_bpm

router = APIRouter()

class BpmAnalyzeRequest(BaseModel):
    youtube_video_id: str
    title: str
    artist: str

class BpmAnalyzeResponse(BaseModel):
    youtube_video_id: str
    bpm: int
    source: str

@router.post("/analyze", response_model=BpmAnalyzeResponse)
def analyze_bpm(req: BpmAnalyzeRequest):
    try:
        bpm, source = process_music_bpm(req.youtube_video_id, req.title, req.artist)
        return BpmAnalyzeResponse(
            youtube_video_id=req.youtube_video_id,
            bpm=bpm,
            source=source
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))