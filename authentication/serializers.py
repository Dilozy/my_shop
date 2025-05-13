from rest_framework import serializers
from django.contrib.auth import authenticate

from .services.auth_service import AuthService, RefreshTokenExpired
from .models import RefreshToken


class CreateJWTSerializer(serializers.Serializer):
    username = serializers.CharField(label="Имя пользователя")
    password = serializers.CharField(label="Пароль", write_only=True)

    def validate(self, data):
        username = data["username"]
        password = data["password"]
        
        user = authenticate(username=username,
                            password=password)
        
        if user is None:
            raise serializers.ValidationError({"error": "Неверный логин или пароль"})
        
        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        refresh_token = AuthService.create_refresh_token(user)
        access_token = AuthService.create_access_token(user)
        return access_token, refresh_token.token


class RefreshJWTSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, data):
        try:
            token_obj = (
                RefreshToken.objects
                .select_related("user")
                .get(
                    token=data["refresh"],
                    is_revoked=False
                )
            )
            
            data["refresh_token_obj"] = token_obj
            data["user"] = token_obj.user
            return data
                
        except RefreshToken.DoesNotExist:
            raise serializers.ValidationError({"error": "Токен не найден или был отозван"})

    def save(self):
        user = self.validated_data["user"]
        refresh_token_obj = self.validated_data["refresh_token_obj"]
        try:
            new_access = AuthService.refresh_access_token(user, refresh_token_obj)
            return new_access
        except RefreshTokenExpired:
            raise
