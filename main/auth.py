# main/auth.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from main.models import Users

class UsersJWTAuthentication(JWTAuthentication):
     def get_user(self, validated_token):
          user_id = validated_token.get("user_id", None)
          if user_id is None:
               return None
          return Users.objects.get(user_id=user_id)
