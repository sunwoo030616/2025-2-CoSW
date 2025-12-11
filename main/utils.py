import requests

AI_BASE = "https://jzybnzxdkntxgmhx.tunnel.elice.io/api/v1"


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
