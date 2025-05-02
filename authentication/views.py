from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from . import serializers
from .services.auth_service import RefreshTokenExpired
from .services.jwt_service import JWT
from .utils import add_to_blacklist
from .models import RefreshToken


class CreateJWTAPIView(APIView):
    def post(self, request):
        serializer = serializers.CreateJWTSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_token, refresh_token = serializer.save()
        return Response({"access_token": access_token,
                         "refresh_token": refresh_token})


class RefreshJWTAPIView(APIView):
    def post(self, request):
        serializer = serializers.RefreshJWTSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            access_token = serializer.save()
            return Response({"access_token": access_token})
        except RefreshTokenExpired as err:
            return Response(
                {"error": str(err)}, status=status.HTTP_401_UNAUTHORIZED
                )


class UserLogoutAPIView(APIView):
    permission_classes = (IsAuthenticated, )
    
    def post(self, request):
        auth_header = request.headers.get("Authorization")
        access_token = auth_header.split()[1]
        _, _, payload = JWT.decode_access_token(access_token)
        username = payload.get("username")
        
        add_to_blacklist(payload.get("jti"), payload.get("exp"))
        
        RefreshToken.objects.select_related("user")\
                            .filter(user__phone_number=username, is_revoked=False)\
                            .update(is_revoked=True)
        
        return Response({"detail": "Произведен выход из системы"})
