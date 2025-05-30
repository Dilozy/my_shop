import hmac

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..services.auth_service import AuthService
from ..utils import is_blacklisted
from cart.services import synchronize_carts


User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = request.headers.get("Authorization")
        
        if not auth:
            return None
        
        token = self.verify_auth_header(auth)
        payload = self.verify_token(token)

        user = self.get_user(payload)
        if user and request.COOKIES.get("cart_id"):
            synchronize_carts(user, request.COOKIES)

        return (user, None)

    def verify_token(self, token):
        sig, expected_sig, payload = AuthService.decode_access_token(token)

        if is_blacklisted(payload.get("jti")):
            raise AuthenticationFailed({"token": "Токен был отозван"})
        
        if not hmac.compare_digest(sig, expected_sig):
            raise AuthenticationFailed({"token": "Неверная сигнатура токена"})
        
        if int(timezone.now().timestamp()) > payload.get("exp"):
            raise AuthenticationFailed({"token": "Токен просрочен"})
        
        return payload
        
    def verify_auth_header(self, auth_header):
        try:
            schema, token = auth_header.split()
            if schema.lower() != "bearer":
                raise AuthenticationFailed({"schema": "Неверная схема авторизации"})
            return token
        except (IndexError, ValueError):
            raise AuthenticationFailed({"token": "Неверный формат заголовка Authorization"})
        
    def get_user(self, payload):
        user = User.objects.filter(phone_number=payload.get("username")).first()
        
        if not user:
            raise AuthenticationFailed({"user":"Пользователь не найден"})
        return user
