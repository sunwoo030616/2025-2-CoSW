import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 1. AI Inference URL
AI_INFER_URL = "https://jzybnzxdkntxgmhx.tunnel.elice.io/api/v1/infer"

# 2. db 저장 개발중
AI_SYNC_URL = "http://localhost:8000/police/sync"
AI_SEARCH_URL = "http://localhost:8000/search"


def call_ai_similarity(description, image_url=None, top_k=3):
    """
    AI inference 서버에 description(or 이미지) 입력하고
    top_k 만큼 유사한 결과 받아오는 함수
    """
    payload = {"text": description, "params": {"top_k": top_k}}

    if image_url:
        payload["image_url"] = image_url

    try:
        response = requests.post(
            AI_INFER_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print("AI 서버 통신 오류:", e)
        return None


# 2. AI Sync 함수 (수정됨: JSON + URL + Raw)
def send_police_data_to_ai(police_dict):
    try:
        payload = {
            "id": police_dict.get("atcId"),
            "name": police_dict.get("fdPrdtNm"),
            "category": police_dict.get("prdtClNm"),
            "custody_place": police_dict.get("depPlace"),
            "date": police_dict.get("fdYmd"),
            "found_place": police_dict.get("fdPlace"),
            "image": police_dict.get("fdFilePathImg"),
            "raw": police_dict,
        }

        response = requests.post(AI_SYNC_URL, json=payload, timeout=5)

        if response.status_code == 200:
            return True
        else:
            print(f"[AI Sync] 실패 (Code {response.status_code}): {response.text}")
            return False

    except Exception as e:
        print(f"[AI Sync] 전송 중 에러: {e}")
        return False


# ---------------------------------------------------------
# 3. 추후 대체
# ---------------------------------------------------------
def get_search_results_from_ai(image_file, text):
    try:
        data = {"text": text}
        files = {}

        # 사용자가 업로드한 이미지가 있는 경우 파일 전송
        if image_file:
            files["image"] = image_file

        response = requests.post(AI_SEARCH_URL, data=data, files=files, timeout=10)

        if response.status_code == 200:
            # AI 반환 구조: { "status": "success", "results": [...] }
            result_json = response.json()
            return result_json.get("results", [])
        else:
            print(f"[Search] AI 검색 실패: {response.text}")
            return []

    except Exception as e:
        print(f"[Search] 검색 요청 중 예외 발생: {e}")
        return []
