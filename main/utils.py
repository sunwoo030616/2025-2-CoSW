import requests

# AI inference server URL
AI_INFER_URL = "https://jzybnzxdkntxgmhx.tunnel.elice.io/api/v1/infer"


def call_ai_similarity(description, image_url=None, top_k=3):
     """
     AI inference 서버에 description(or 이미지) 입력하고
     top_k 만큼 유사한 결과 받아오는 함수
     """

     payload = {
          "text": description,
          "params": {"top_k": top_k}
     }

     # 이미지 URL도 필요하면 추가 (AI 개발자와 약속한 스펙에 따라 수정 가능)
     if image_url:
          payload["image_url"] = image_url

     try:
          response = requests.post(
               AI_INFER_URL,
               headers={"Content-Type": "application/json"},
               json=payload,
               timeout=10
          )
          response.raise_for_status()
          return response.json()  # 보통 {"results": [ ... ]}

     except Exception as e:
          print("AI 서버 통신 오류:", e)
          return None
