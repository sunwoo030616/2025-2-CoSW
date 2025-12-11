import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


AI_BASE = "https://jzybnzxdkntxgmhx.tunnel.elice.io/api/v1"

# db 저장 개발중
AI_SYNC_URL = "http://localhost:8000/police/sync"
AI_SEARCH_URL = "http://localhost:8000/search"


def ai_infer(description, top_k=3):
    """
    /pipeline/infer 는 즉시 결과(top 리스트)를 반환
    Django에서는 이 결과를 그대로 formatted matches 로 변환
    """
    payload = {
        "text": description,
        "top_k": top_k
    }

    try:
        res = requests.post(
            f"{AI_BASE}/pipeline/infer",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        print("🔥 [infer raw]", res.text)
        res.raise_for_status()
    except Exception as e:
        print("🔥 infer 호출 실패:", e)
        return []

    try:
        data = res.json()
    except:
        print("🔥 infer 응답 JSON 파싱 실패")
        return []

    return data.get("top", [])


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
