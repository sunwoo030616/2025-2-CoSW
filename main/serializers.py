from rest_framework import serializers
from .models import Users


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ["email"]

    # 이메일 중복 체크
    def validate_email(self, value):
        if Users.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 가입된 이메일입니다.")
        return value


# 로그인 요청 데이터 검증
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
