from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser

from .models import *
from .serializers import *
from .utils import *
from django.db import connection


class AuthEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserEmailSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # 1) 해당 이메일의 유저가 있는지 확인
            user, created = Users.objects.get_or_create(email=email)

            # 2) JWT 발급
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "created": created,  # True면 이번 요청에서 새 회원가입됨
                    "access_token": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# 분실물 등록 + AI 유사도 검색 API
class LostItemCreateView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = LostItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = serializer.validated_data.get("image")
        description = serializer.validated_data.get("description")

        # TODO: S3 업로드 예정 → 현재는 로컬 경로 저장
        image_url = None
        if image:
            image_url = f"/uploads/{image.name}"

        # DB 저장 (embedding은 None)
        lost_item = UserLostItem.objects.create(
            user=request.user,
            description=description,
            original_image_url=image_url,
            vlm_embedding=None
        )

        # AI inference 서버에 유사도 검색 요청
        ai_results = call_ai_similarity(
            description=description,
            image_url=image_url,
            top_k=3
        )

        # AI 서버 응답 처리
        matches = []
        if ai_results:
            # AI 팀이 JSON을 {"results": [...]} 형태로 준다는 전제
            matches = ai_results.get("results", ai_results)

        return Response(
            {
                "registered_item": {
                    "request_id": lost_item.request_id,
                    "description": lost_item.description,
                    "original_image_url": lost_item.original_image_url,
                    "is_active": lost_item.is_active,
                    "created_at": lost_item.created_at,
                },
                "immediate_matches": matches,
            },
            status=status.HTTP_201_CREATED
        )


# GET 사용자가 등록한 아이템 목록
class ItemsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        items = UserLostItem.objects.filter(user=user).order_by("-created_at")
        serializer = UserLostItemListSerializer(items, many=True)

        return Response({"items": serializer.data}, status=200)


# PATCH 분실물 알림 중지
class CeaseLostItemView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, request_id):
        try:
            lost_item = UserLostItem.objects.get(request_id=request_id, user=request.user)
        except UserLostItem.DoesNotExist:
            return Response(
                {"error": "해당 요청이 존재하지 않거나 권한이 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        lost_item.is_active = False
        lost_item.save()

        return Response(
            {
                "request_id": request_id,
                "message": "알림이 중지되었습니다."
            },
            status=status.HTTP_200_OK
        )