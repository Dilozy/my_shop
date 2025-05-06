import pytest
import hmac
import uuid

from authentication.services.auth_service import AuthService, RefreshTokenExpired
from authentication.models import RefreshToken


@pytest.mark.django_db
class TestJWTService:
    def test_create_access_token(self, test_user):
        test_access = AuthService.create_access_token(test_user)
        assert isinstance(test_access, str), "Неверный формат токена"
        assert len(test_access.split(".")) == 3, "Нарушена структура токена"

    def test_decode_access_token(self, test_user, auth_tokens):
        test_access = auth_tokens["access_token"]
        
        decoded_data = AuthService.decode_access_token(test_access)
        assert len(decoded_data) == 3, "Нарушена структура токена"
        
        sig, expected_sig, payload = decoded_data        
        assert hmac.compare_digest(sig, expected_sig), "Неверная сигнатура токена"

        assert len(payload) == 5, "Полезные данные токена повреждены"
        assert payload.get("username") == test_user.phone_number, (
        f"Данные из токена не совпадают с данными юзера: Токен: {payload.get('username')},"
        f"Юзер: {test_user.phone_number}"
        )
        
        assert payload.get("email") == test_user.email, (
        f"Данные из токена не совпадают с данными юзера: Токен: {payload.get('email')},"
        f"Юзер: {test_user.email}"
        )
        
        assert payload.get("sub") == test_user.id, (
        f"Данные из токена не совпадают с данными юзера: Токен: {payload.get('sub')},"
        f"Юзер: {test_user.id}"
        )

    def test_create_refresh_token(self, test_user, auth_tokens):
        test_refresh = auth_tokens["refresh_token"].token

        assert isinstance(test_refresh, str), "Неверный формат токена обновления"

        refresh_from_db = RefreshToken.objects.filter(user=test_user, is_revoked=False).first()
        assert str(refresh_from_db.token) == str(test_refresh), "Токены обновления не совпадают"

        assert refresh_from_db.user == test_user, "Пользователи не совпадают"
        assert not refresh_from_db.is_revoked, "Токен уже был отозван"

    def test_refresh_access_token_with_valid_refresh_token(self,
                                                           test_user,
                                                           auth_tokens):
        old_access_token = auth_tokens["access_token"]
        new_access_token = AuthService.refresh_access_token(test_user, auth_tokens["refresh_token"])
        
        assert new_access_token is not None, "Не удалось обновить access token"
        assert new_access_token != old_access_token, "Новый access token должен отличаться от старого"
        
        auth_tokens["access_token"] = new_access_token
        
        try:
            self.test_decode_access_token(test_user, auth_tokens)
        except Exception as e:
            pytest.fail(f"Ошибка при декодировании обновленного токена: {str(e)}")

    def test_refresh_access_token_with_invalid_refresh_token(self, test_user):
        revoked_refresh = AuthService.create_refresh_token(test_user)
        revoked_refresh.is_revoked = True
        revoked_refresh.save()
        
        with pytest.raises(
            RefreshTokenExpired,
            match="Время жизни токена истекло. Пройдите процедуру авторизации заново."
        ):
            AuthService.refresh_access_token(test_user, revoked_refresh)

    def test_invalidate_refresh_token(self, auth_tokens):
        AuthService.invalidate_refresh_token(auth_tokens["refresh_token"])

        assert auth_tokens["refresh_token"].is_revoked




