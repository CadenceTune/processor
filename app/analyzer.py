import os
import re
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

class BpmAnalyzer:
    def __init__(self):
        self.getsongbpm_api_key = os.getenv("GETSONGBPM_API_KEY")
        
        # HTTP Connection Pool 재사용을 위한 Session 객체 생성 (속도 극대화)
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://songbpm.com",
            "referer": "https://songbpm.com/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })

    def _clean_text(self, text: str) -> str:
        """검색 성공률을 높이기 위해 특수문자, 괄호, 피처링, MV 등 잡어를 정제합니다."""
        if not text:
            return ""
        cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', text)
        cleaned = re.sub(r'(?i)(official|music|video|mv|prod\.?|feat\.?|ft\.?)', '', cleaned)
        cleaned = cleaned.replace("- Topic", "")
        cleaned = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣぁ-ゔァ-ヴー一-龥]', ' ', cleaned)
        return cleaned.strip()

    def get_bpm(self, title: str, artist: str = "", youtube_url: str = None) -> float:
        clean_title = self._clean_text(title)
        clean_artist = self._clean_text(artist)

        # ------------------------------------------------------------------
        # 1차 시도: SongBPM.com POST 파싱 (정제된 아티스트 + 곡명)
        # ------------------------------------------------------------------
        try:
            bpm = self._fetch_from_songbpm_post(clean_title, clean_artist)
            if bpm and bpm > 0:
                print(f"[SongBPM.com 성공] {clean_artist} - {clean_title} : {bpm} BPM")
                return float(bpm)
        except Exception as e:
            print(f"[SongBPM.com 1차 실패] 사유: {e}")

        # ------------------------------------------------------------------
        # 2차 시도: SongBPM.com POST 파싱 (곡명 단독)
        # ------------------------------------------------------------------
        if clean_artist and clean_title:
            try:
                bpm = self._fetch_from_songbpm_post(clean_title, "")
                if bpm and bpm > 0:
                    print(f"[SongBPM.com 2차(제목단독) 성공] {clean_title} : {bpm} BPM")
                    return float(bpm)
            except Exception as e:
                print(f"[SongBPM.com 2차 실패] 사유: {e}")

        # ------------------------------------------------------------------
        # 3차 시도: GetSongBPM API Fallback
        # ------------------------------------------------------------------
        if self.getsongbpm_api_key:
            try:
                bpm = self._fetch_from_getsongbpm_api(clean_title, clean_artist)
                if bpm and bpm > 0:
                    print(f"[GetSongBPM API 성공] {clean_artist} - {clean_title} : {bpm} BPM")
                    return float(bpm)
            except Exception:
                pass

        print(f"[BPM 최종 미조회] {artist} - {title} -> 0.0 반환")
        return 0.0

    def _fetch_from_songbpm_post(self, title: str, artist: str) -> float:
        """SongBPM.com에 POST 요청을 날려 정확한 DOM 영역에서 BPM 숫자 추출"""
        url = "https://songbpm.com/searches"
        query_str = f"{artist} {title}".strip() if artist else title
        payload = {"query": query_str}

        time.sleep(0.3)  # 과도한 연속 요청 방지
        # 타임아웃을 10초로 늘리고 session 재사용
        response = self.session.post(url, data=payload, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # DOM 구조 분석 기반 핀포인트 파싱
            bpm_label_spans = soup.find_all("span", text=re.compile(r'^\s*BPM\s*$', re.IGNORECASE))
            
            for span in bpm_label_spans:
                parent_div = span.parent
                if parent_div:
                    bpm_val_span = parent_div.find("span", class_=re.compile(r'text-2xl|font-bold|text-3xl'))
                    if bpm_val_span:
                        raw_text = bpm_val_span.get_text().strip()
                        if raw_text.isdigit():
                            val = float(raw_text)
                            if 40.0 <= val <= 240.0:
                                return val

            # Fallback 정규식 파싱
            match = re.search(r'BPM</span>\s*<span[^>]*>\s*(\d{2,3})\s*</span>', response.text, re.IGNORECASE)
            if match:
                return float(match.group(1))

        return None

    def _fetch_from_getsongbpm_api(self, title: str, artist: str) -> float:
        url = "https://api.getsong.co/search/"
        lookup_query = f"song:{title} artist:{artist}".strip() if artist else title
        params = {
            'api_key': self.getsongbpm_api_key,
            'type': 'both' if artist else 'song',
            'lookup': lookup_query
        }
        time.sleep(0.3)
        res = self.session.get(url, params=params, timeout=10)
        if res.status_code == 200 and not res.text.startswith("<"):
            songs = res.json().get("search", [])
            if songs and songs[0].get("tempo"):
                return float(songs[0].get("tempo"))
        return None