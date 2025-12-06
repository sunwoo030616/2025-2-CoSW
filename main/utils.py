import requests
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# AI 서버 주소 (배포 시 환경변수로 분리 권장)
AI_SYNC_URL = "http://localhost:8000/police/sync"  # 데이터 적재 API
AI_SEARCH_URL = "http://localhost:8000/search"  # 검색 API


# 경찰청 신규 데이터 AI 서버로 전송 (multipart/form-data)
# data: db_id(atc_id) + text(사물 이름 + 묘사)
# files: 이미지가 존재 할 때만 파일로 저장해서 넘김
def send_new_item_to_ai(item_obj):
    try:
        data = {
            "db_id": item_obj.atc_id,
            "text": f"{item_obj.item_name} {item_obj.item_desc}".strip(),
        }

        files = {}

        if item_obj.police_image_url:
            try:
                img_response = requests.get(
                    item_obj.police_image_url, stream=True, verify=False, timeout=20
                )

                if img_response.status_code == 200:
                    files["image"] = ("image.jpg", img_response.content, "image/jpeg")
                else:
                    print(
                        f"[Sync] 이미지 다운로드 실패 (Status: {img_response.status_code}) -> 텍스트만 전송. ID: {item_obj.atc_id}"
                    )
            except Exception as e:
                print(
                    f"[Sync] 이미지 다운로드 중 에러 -> 텍스트만 전송. ID: {item_obj.atc_id}, Err: {e}"
                )

        # files가 비어있으면 AI 서버의 'image' 필드는 None으로 처리됨
        response = requests.post(AI_SYNC_URL, data=data, files=files)

        if response.status_code == 200:
            has_img = "O" if files else "X"
            print(f"[Sync] AI 전송 성공: {item_obj.atc_id} (이미지: {has_img})")
            return True
        else:
            print(f"[Sync] AI 서버 에러: {response.text}")
            return False

    except Exception as e:
        print(f"[Sync] 전송 요청 중 예외 발생: {e}")
        return False


# 개발중인 매칭 로직으로 부분 대체 예정
def get_search_results_from_ai(image_file, text):

    try:
        data = {"text": text}
        files = {}

        # 사용자가 업로드한 이미지가 있는 경우 파일 전송
        if image_file:
            files["image"] = image_file

        response = requests.post(AI_SEARCH_URL, data=data, files=files)

        if response.status_code == 200:
            # AI 반환 JSON 구조: { "status": "success", "results": [...] }
            result_json = response.json()
            return result_json.get("results", [])
        else:
            print(f"[Search] AI 검색 실패: {response.text}")
            return []

    except Exception as e:
        print(f"[Search] 검색 요청 중 예외 발생: {e}")
        return []
