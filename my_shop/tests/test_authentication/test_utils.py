import pytest

from authentication.services.auth_service import AuthService
from authentication.utils import add_to_blacklist, is_blacklisted


@pytest.mark.django_db
class TestUtils:
    def test_blacklist(self, test_user):
        access_token = AuthService.create_access_token(test_user)
        _, _, payload = AuthService.decode_access_token(access_token)

        token_jti = payload.get("jti")
        token_exp = payload.get("exp")
        
        assert token_jti is not None, "Неверный формат подписи: отсутствует поле 'jti'"
        assert token_exp is not None, "Неверный формат подписи: отсутствует поле 'exp'"

        add_to_blacklist(payload.get("jti"), payload.get("exp"))

        assert is_blacklisted(token_jti), "Токен не был успешно добавлен в черный список"
