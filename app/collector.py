import os
import requests
from urllib.parse import parse_qs, urlparse
from dotenv import load_dotenv

load_dotenv()

# 1. 클래스를 먼저 정의합니다.
class PlaylistCollector:
    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")

    def _extract_playlist_id(self, url: str) -> str:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        playlist_ids = query_params.get("list")
        return playlist_ids[0] if playlist_ids else None

    def fetch_playlist_tracks(self, playlist_url: str) -> list:
        playlist_id = self._extract_playlist_id(playlist_url)
        if not playlist_id or not self.youtube_api_key:
            print("[Collector Error] 올바르지 않은 URL이거나 API Key가 없습니다.")
            return []

        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        tracks = []
        next_page_token = None

        try:
            while True:
                params = {
                    "part": "snippet",
                    "maxResults": 50,
                    "playlistId": playlist_id,
                    "key": self.youtube_api_key
                }
                if next_page_token:
                    params["pageToken"] = next_page_token

                response = requests.get(url, params=params, timeout=10)
                if response.status_code != 200:
                    print(f"[YouTube API 에러] 응답 코드: {response.status_code}")
                    break

                data = response.json()
                for item in data.get("items", []):
                    snippet = item.get("snippet", {})
                    resource_id = snippet.get("resourceId", {})
                    youtube_id = resource_id.get("videoId", "")

                    title = snippet.get("title", "")
                    if title in ["Private video", "Deleted video"]:
                        continue

                    artist = snippet.get("videoOwnerChannelTitle", "") or snippet.get("channelTitle", "")
                    video_url = f"https://www.youtube.com/watch?v={youtube_id}"
                    
                    thumbnails = snippet.get("thumbnails", {})
                    high_thumb = thumbnails.get("high", {}) or thumbnails.get("default", {})
                    thumbnail_url = high_thumb.get("url", f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg")

                    tracks.append({
                        "youtube_id": youtube_id,
                        "title": title,
                        "artist": artist,
                        "url": video_url,
                        "duration": 0,
                        "thumbnail_url": thumbnail_url,
                        "bpm": 0.0
                    })

                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break

            print(f"[Collector Success] 총 {len(tracks)}개 메타데이터 수집 성공")

        except Exception as e:
            print(f"[Collector Exception] 사유: {e}")
            raise e

        return tracks

# 2. 인스턴스 생성이 필요하다면 클래스 정의 아래에 둡니다.
# (main.py에서 collector = PlaylistCollector()로 생성 중이라면 아래 줄은 지워도 무방합니다)
collector = PlaylistCollector()