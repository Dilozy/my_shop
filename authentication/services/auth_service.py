from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import APIException

from ..models import RefreshToken
from .jwt_service import JWT


class RefreshTokenExpired(APIException):
    status_code = 401
    default_detail = "Время жизни токена истекло. Пройдите процедуру авторизации заново."


class AuthService:
    @staticmethod
    def create_refresh_token(user):
        """Создаёт новый refresh-токен"""
        token_obj = RefreshToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(days=7)
            )
        return token_obj.token

    @staticmethod
    def refresh_access_token(user, refresh_token):
        if AuthService._is_refresh_token_valid(refresh_token):
            return JWT.create_access_token(user)
        else:
            AuthService.invalidate_refresh_token(refresh_token)
            raise RefreshTokenExpired()

    @staticmethod
    def _is_refresh_token_valid(token_obj):
        """Проверяет, что токен не просрочен"""
        return token_obj.expires_at > timezone.now()

    @staticmethod
    def invalidate_refresh_token(token_obj):
        """Помечает токен как отозванный"""
        token_obj.is_revoked = True
        token_obj.save()

