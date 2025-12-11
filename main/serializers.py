from rest_framework import serializers
from .models import *


class UserEmailSerializer(serializers.Serializer):
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