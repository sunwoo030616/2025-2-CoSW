import requests
import os
import random
import xmltodict
import urllib3
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from main.models import PoliceFoundItem
from main.models import UserLostItem, PoliceFoundItem, NotificationLog
from pgvector.django import CosineDistance
from django.db.models import F

# SSL 경고 끄기
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# [가짜 AI 함수]
def get_fake_embedding():
    return [random.random() for _ in range(768)]


class EmailSendView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        recipient = request.data.get("to")
        subject = request.data.get("subject")
        body = request.data.get("body")

        # 필수 값 체크
        if not recipient or not subject or not body:
            return Response({"error": "to, subject, body are required"}, status=400)

        # 이메일 전송 로직
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=None,
                recipient_list=[recipient],
                fail_silently=False,
            )
            return Response({"status": "sent"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


# POST /internal/found-items/sync
class FoundItemSyncView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        api_key = os.getenv("POLICE_API_KEY")

        if not api_key:
            return Response({"error": "POLICE_API_KEY not found in .env"}, status=500)
        base_url = "http://apis.data.go.kr/1320000/LosfundInfoInqireService/getLosfundInfoAccToClAreaPd"

        # 날짜 계산 (Ai 연결 후 30일치 받고 1일로 변경)
        today = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=14)).strftime("%Y%m%d")

        params = {
            "serviceKey": api_key,
            "START_YMD": start_date,
            "END_YMD": today,
            "numOfRows": "20",  # 20개 가져옴 - 추후 갯수 변경예정
            "pageNo": "1",
        }

        # 요청
        try:
            response = requests.get(base_url, params=params, verify=False)

            if response.status_code != 200:
                return Response(
                    {
                        "error": f"API Error: {response.status_code}",
                        "detail": response.text,
                    },
                    status=502,
                )

            # 데이터 파싱 - JSON 시도 후 XML
            items_list = []
            try:
                data = response.json()
                items_body = data["response"]["body"]["items"]
                if items_body:
                    items_list = items_body["item"]
            except Exception:
                try:
                    data_dict = xmltodict.parse(response.content)
                    response_body = data_dict.get("response", {}).get("body", {})
                    items_wrapper = response_body.get("items")
                    if items_wrapper:
                        items_list = items_wrapper.get("item")
                except Exception as e:
                    return Response(
                        {"error": "Parsing Failed", "detail": str(e)}, status=502
                    )

            # 리스트 정규화
            if isinstance(items_list, dict):
                items_list = [items_list]
            elif items_list is None:
                items_list = []

            saved_count = 0

            # DB 저장
            for item in items_list:
                try:
                    atc_id = item.get("atcId")
                    fd_sn = item.get("fdSn")

                    if not atc_id or not fd_sn:
                        continue

                    fd_ymd_str = item.get("fdYmd")
                    found_date_obj = None
                    if fd_ymd_str:
                        try:
                            fmt = "%Y-%m-%d" if "-" in fd_ymd_str else "%Y%m%d"
                            found_date_obj = datetime.strptime(fd_ymd_str, fmt).date()
                        except ValueError:
                            found_date_obj = None

                    i_name = item.get("fdPrdtNm", "이름 없음") or ""
                    i_desc = item.get("fdSbjt", "") or ""
                    i_loc = item.get("depPlace", "") or ""
                    i_img = item.get("fdFilePathImg", "") or ""

                    obj, created = PoliceFoundItem.objects.update_or_create(
                        atc_id=atc_id,
                        fd_sn=fd_sn,
                        defaults={
                            "item_name": i_name[:195],  # 200자 제한 -> 안전하게 195자
                            "item_desc": i_desc,  # TextField
                            "found_location": i_loc[:195],  # 195자 제한
                            "found_date": found_date_obj,  # 날짜 객체
                            "police_image_url": i_img[:495],  # 495자 제한 -> 490자
                            "vlm_embedding": get_fake_embedding(),
                        },
                    )
                    if created:
                        saved_count += 1

                except Exception as db_err:
                    print(f"저장 실패 ({atc_id}): {db_err}")
                    continue

            return Response(
                {"new_items": saved_count, "synced_at": timezone.now().isoformat()},
                status=200,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=500)


# POST /internal/matching/daily
class DailyMatchingView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            lost_items = UserLostItem.objects.filter(is_active=True).exclude(
                vlm_embedding__isnull=True
            )

            # 테스트용: 1.0 (무조건 매칭), [실전용] 0.25 (유사도 약 75% 이상)
            SIMILARITY_THRESHOLD = 1.0

            for lost in lost_items:
                try:
                    if lost.vlm_embedding is None:
                        continue

                    try:
                        user_vector = list(lost.vlm_embedding)
                    except:
                        user_vector = lost.vlm_embedding

                    # 유사 습득물 3개
                    candidates = PoliceFoundItem.objects.annotate(
                        distance=CosineDistance("vlm_embedding", user_vector)
                    ).order_by("distance")[:3]

                    valid_matches = []
                    for item in candidates:
                        if item.distance is None:
                            continue
                        if item.distance > SIMILARITY_THRESHOLD:
                            continue

                        already_sent = NotificationLog.objects.filter(
                            user=lost.user,
                            request=lost,
                            atc_id=item.atc_id,
                            fd_sn=item.fd_sn,
                        ).exists()

                        if not already_sent:
                            valid_matches.append(item)

                    if not valid_matches:
                        continue

                    # 이메일 본문
                    match_list_text = ""
                    for idx, match in enumerate(valid_matches, 1):
                        similarity = (1 - match.distance) * 100
                        match_list_text += f"""
                        [{idx}번째 후보]
                        - 물품명: {match.item_name}
                        - 보관장소: {match.found_location}
                        - 습득일자: {match.found_date}
                        - 유사도: {similarity:.1f}%
                        - 사진 보기: {match.police_image_url}
                        ----------------------------------------
                        """

                    subject = f"[Lost112] '{lost.description[:10]}...'와(과) 유사한 물건 {len(valid_matches)}개를 찾았습니다!"
                    body = f"""
                    안녕하세요, {lost.user.email}님.
                    등록하신 분실물과 유사한 습득물이 발견되었습니다.
                    
                    ========================================
                    {match_list_text}
                    ========================================
                    """

                    # 이메일 발송
                    send_mail(
                        subject=subject,
                        message=body,
                        from_email=None,
                        recipient_list=[lost.user.email],
                        fail_silently=False,
                    )

                    # 로그 저장
                    for match in valid_matches:
                        NotificationLog.objects.create(
                            user=lost.user,
                            request=lost,
                            atc_id=match.atc_id,
                            fd_sn=match.fd_sn,
                            similarity_score=(1 - match.distance),
                            is_sent=True,
                        )

                    print(f"[Success] Email sent to {lost.user.email}")

                except Exception as inner_e:
                    print(f"[Error] Item ID {lost.request_id}: {inner_e}")
                    continue

            # 성공
            return Response({"status": "sent"}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
