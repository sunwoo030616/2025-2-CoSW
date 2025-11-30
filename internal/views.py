from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


# POST /internal/email/send
class EmailSendView(APIView):
    permission_classes = [AllowAny]  # 개발 중

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
