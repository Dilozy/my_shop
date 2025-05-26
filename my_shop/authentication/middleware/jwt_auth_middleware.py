import hmac

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..services.auth_service import AuthService
from ..utils import is_blacklisted


User = get_user_model()


class JWTAuthMiddleware(BaseAuthentication):
    def authenticate(self, request):
        auth = request.headers.get("Authorization")

        if not auth:
            return None
        
        try:
            schema, token = auth.split()
            if schema.lower() != "bearer":
                raise ValueError
        except (IndexError, ValueError):
            return None

        sig, expected_sig, payload = AuthService.decode_access_token(token)
        self.verify_access_token(sig, expected_sig, payload)

        if is_blacklisted(payload.get("jti")):
            raise AuthenticationFailed({"error": "Токен был отозван"})
        
        user = User.objects.filter(phone_number=payload.get("username")).first()
        
        if not user:
            raise AuthenticationFailed("Пользователь не найден")

        return (user, None)

    def verify_access_token(self, sig, expected_sig, payload):
        if not hmac.compare_digest(sig, expected_sig):
            raise AuthenticationFailed({"error": "Неверная сигнатура токена"})
        
        if int(timezone.now().timestamp()) > payload.get("exp"):
            raise AuthenticationFailed({"error": "Токен просрочен"})
        
