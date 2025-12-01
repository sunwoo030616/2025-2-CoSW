from rest_framework import serializers
from .models import *


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


# 분실물 검색
class LostItemCreateSerializer(serializers.Serializer):
    image = serializers.ImageField(required=False)
    description = serializers.CharField(required=False)

    def validate(self, data):
        if not data.get("image") and not data.get("description"):
            raise serializers.ValidationError("이미지 또는 설명 중 하나는 필요합니다.")
        return data
    

class UserLostItemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLostItem
        fields = [
            "request_id",
            "description",
            "original_image_url",
            "is_active",
            "created_at",
        ]