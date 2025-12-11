import requests
import os
import xmltodict
from datetime import datetime, timedelta
import urllib3

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.core.mail import send_mail
from django.db import connection

from main.models import PoliceFoundItem, UserLostItem, NotificationLog
from main.utils import ai_infer, send_police_data_to_ai

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 1. 이메일 발송 (유틸성 뷰)
class EmailSendView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        recipient = request.data.get("to")
        subject = request.data.get("subject")
        body = request.data.get("body")

        if not recipient or not subject or not body:
            return Response({"error": "to, subject, body are required"}, status=400)

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


# 2. 경찰청 데이터 동기화 (크롤러 역할)
class FoundItemSyncView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        api_key = os.getenv("POLICE_API_KEY")
        if not api_key:
            return Response({"error": "POLICE_API_KEY is missing"}, status=500)

        # 1. 파라미터 파싱
        days_ago = int(request.data.get("days", 1))
        num_rows = int(request.data.get("rows", 1000))
        page_no = int(request.data.get("page", 1))

        today = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d")

        # 2. 경찰청 API 호출
        base_url = "http://apis.data.go.kr/1320000/LosfundInfoInqireService/getLosfundInfoAccToClAreaPd"
        params = {
            "serviceKey": api_key,
            "START_YMD": start_date,
            "END_YMD": today,
            "numOfRows": str(num_rows),
            "pageNo": str(page_no),
        }

        try:
            response = requests.get(base_url, params=params, verify=False)

            # 3. XML 파싱
            items_list = []
            try:
                data_dict = xmltodict.parse(response.content)
                items_wrapper = (
                    data_dict.get("response", {}).get("body", {}).get("items")
                )
                if items_wrapper:
                    items_list = items_wrapper.get("item")
            except Exception:
                pass

            if isinstance(items_list, dict):
                items_list = [items_list]
            elif items_list is None:
                items_list = []

            saved_count = 0
            sent_ai_count = 0

            # 4. 데이터 처리 루프
            for item in items_list:
                atc_id = item.get("atcId")
                fd_sn = item.get("fdSn")
                if not atc_id:
                    continue

                # --- [날짜 변환 및 포맷 강제 적용] ---
                fd_ymd = item.get("fdYmd")
                found_date = None

                if fd_ymd:
                    try:
                        # 하이픈 유무 확인 후 날짜 객체 변환
                        fmt = "%Y-%m-%d" if "-" in fd_ymd else "%Y%m%d"
                        dt_obj = datetime.strptime(fd_ymd, fmt).date()

                        # (1) DB 저장용 (Python Date 객체)
                        found_date = dt_obj

                        # (2) AI 전송용 (YYYY-MM-DD 문자열로 강제 변환)
                        item["fdYmd"] = dt_obj.strftime("%Y-%m-%d")
                    except Exception:
                        pass
                # ------------------------------------

                raw_img_url = item.get("fdFilePathImg", "")
                final_img_url = raw_img_url[:490] if raw_img_url else None

                # DB 저장 (Upsert)
                obj, created = PoliceFoundItem.objects.update_or_create(
                    atc_id=atc_id,
                    fd_sn=fd_sn,
                    defaults={
                        "item_name": item.get("fdPrdtNm", "")[:190],
                        "item_desc": item.get("fdSbjt", ""),
                        "found_location": item.get("depPlace", "")[:190],
                        "found_date": found_date,
                        "police_image_url": final_img_url,
                        "raw_data": item,
                    },
                )

                # 신규 데이터라면 AI로 전송 (utils 함수 사용)
                if created:
                    saved_count += 1
                    # item['fdYmd']는 위에서 "2025-12-11" 포맷으로 변경됨
                    if send_police_data_to_ai(item):
                        sent_ai_count += 1

            return Response(
                {
                    "message": "Daily Sync Complete",
                    "date_range": f"{start_date} ~ {today}",
                    "total_fetched": len(items_list),
                    "new_db_saved": saved_count,
                    "sent_to_ai": sent_ai_count,
                },
                status=200,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=500)


# 3. 데일리 매칭 (Batch Job)
class DailyMatchingView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. 활성화된 요청 조회
        active_requests = UserLostItem.objects.filter(is_active=True)

        processed_count = 0
        email_sent_count = 0

        for lost_req in active_requests:
            try:
                # [설정] AI Infer 호출 (Top 3)
                ai_results = ai_infer(lost_req.description, top_k=3)

                if not ai_results:
                    continue

                new_matches = []

                # 중복 알림 방지 및 필터링
                for idx, match in enumerate(ai_results):
                    # 필드 매핑
                    match_id = str(match.get("atcId"))
                    match_name = match.get("fdPrdtNm", "이름 없음")
                    score = match.get("score", 0)
                    rank = idx + 1  # 1위, 2위, 3위...

                    # DB 로그 확인
                    already_sent = NotificationLog.objects.filter(
                        request=lost_req, atc_id=match_id, is_sent=True
                    ).exists()

                    # 보낸 적 없다면 리스트에 추가
                    if not already_sent:
                        new_matches.append(
                            {
                                "id": match_id,
                                "name": match_name,
                                "score": score,
                                "rank": rank,
                            }
                        )

                # 새로운 매칭 결과가 있다면 이메일 발송
                if new_matches:
                    email_subject = (
                        f"[Lost112] '{lost_req.description}' 관련 습득물 알림"
                    )

                    email_body = f"안녕하세요.\n요청하신 '{lost_req.description}'과 유사한 습득물이 발견되었습니다.\n\n"
                    for item in new_matches:
                        email_body += (
                            f"[{item['rank']}위] 유사도: {item['score']:.2f}\n"
                        )
                        email_body += f"- 물품명: {item['name']}\n"
                        email_body += f"- 관리번호: {item['id']}\n"
                        email_body += "--------------------------------\n"

                    email_body += "\n경찰청 유실물 포털(Lost112)에서 관리번호로 검색하여 상세 정보를 확인하세요."

                    # [실제 발송]
                    try:
                        send_mail(
                            subject=email_subject,
                            message=email_body,
                            from_email=None,
                            recipient_list=[lost_req.user.email],
                            fail_silently=False,
                        )
                        email_sent_count += 1

                        # 발송 성공 시 로그 저장
                        for item in new_matches:
                            NotificationLog.objects.create(
                                user=lost_req.user,
                                request=lost_req,
                                atc_id=item["id"],
                                rank=item["rank"],
                                similarity_score=item["score"],
                                is_sent=True,
                            )

                    except Exception as e:
                        print(f"Email Error ({lost_req.user.email}): {e}")

                processed_count += 1

            except Exception as e:
                print(f"Matching Error ({lost_req.request_id}): {e}")
                continue

        return Response(
            {
                "status": "Job Done",
                "processed_requests": processed_count,
                "emails_sent": email_sent_count,
            },
            status=200,
        )
