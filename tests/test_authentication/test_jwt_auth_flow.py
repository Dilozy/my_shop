import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from authentication.services.auth_service import AuthService
from authentication.models import RefreshToken
from authentication.utils import is_blacklisted


User = get_user_model()


@pytest.mark.django_db
class TestJWTFlow:
    
    @property
    def obtain_jwt_endpoint(self):
        return reverse("auth:obtain_jwt")
    
    @property
    def refresh_jwt_endpoint(self):
        return reverse("auth:refresh_jwt")
    
    @property
    def logout_endpoint(self):
        return reverse("auth:logout")

    def test_create_jwt_flow(self, test_user, auth_tokens):
        access_token = auth_tokens.get("access_token")
        assert access_token, "Access token отсутствует в ответе"
        
        sig, expected_sig, payload = AuthService.decode_access_token(access_token)
        assert sig == expected_sig, "Невалидная подпись токена"
        assert payload["username"] == test_user.phone_number, "Неверный username в payload"
        assert payload["email"] == test_user.email, "Неверный email в payload"
        
        refresh_token = auth_tokens.get("refresh_token").token
        assert refresh_token, "Refresh token отсутствует в ответе"
        
        db_refresh_token = RefreshToken.objects.filter(
            user__phone_number=test_user.phone_number
        ).first()
        
        assert db_refresh_token, "Refresh token не сохранён в БД"
        assert refresh_token == db_refresh_token.token, "Несоответствие refresh token"

    def test_refresh_jwt_flow(self, api_client, test_user, auth_tokens):
        curr_refresh_token = auth_tokens.get("refresh_token").token
        assert curr_refresh_token is not None, "Access token отсутствует в ответе"

        response_refresh = api_client.post(
            self.refresh_jwt_endpoint,
            data={"refresh": curr_refresh_token},
            format="json"
        )

        assert response_refresh.status_code == 200, (
            f"Ошибка. Ответ: {response_refresh.json()}"
        )

        response_refresh_data = response_refresh.json()

        assert response_refresh_data.get("access_token") is not None, (
            "Access token отсутствует в ответе"
            )

        new_access_token = response_refresh_data.get("access_token")

        sig, expected_sig, payload = AuthService.decode_access_token(new_access_token)
        assert sig == expected_sig, "Невалидная подпись токена"
        assert payload["username"] == test_user.phone_number, "Неверный username в payload"
        assert payload["email"] == test_user.email, "Неверный email в payload"

    def test_destroy_jwt_flow(self, api_client, test_user, auth_tokens):
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_tokens['access_token']}")

        response = api_client.post(
            self.logout_endpoint
        )
        assert response.status_code == 200, (
            f"Ошибка. Ответ: {response.json()}"
        )

        response_data = response.json()
        assert response_data.get("detail") is not None, "Неверный формат ответа"
        assert response_data.get("detail") == "Произведен выход из системы"

        assert RefreshToken.objects.get(token=auth_tokens["refresh_token"].token).is_revoked

        _, _, payload = AuthService.decode_access_token(auth_tokens["access_token"])
        assert is_blacklisted(payload["jti"])
        assert payload.get("username") == test_user.phone_number








