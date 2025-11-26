from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Users
from .serializers import UserRegisterSerializer, UserLoginSerializer


def ping(request):
    return JsonResponse({"status": "ok", "message": "pong"})


# POST /auth/register
class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "access_token": str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# POST /auth/login
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = Users.objects.get(email=email)
            except Users.DoesNotExist:
                return Response(
                    {"error": "존재하지 않는 이메일입니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            refresh = RefreshToken.for_user(user)
            return Response(
                {"access_token": str(refresh.access_token)}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
