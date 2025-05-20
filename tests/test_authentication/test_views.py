from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from authentication.models import RefreshToken


@pytest.mark.django_db
class TestCreateJWTAPIView:
    @property
    def endpoint(self):
        return reverse("auth:obtain_jwt")
    
    def test_view_with_correct_request(self, api_client, test_user):
        data = {"username": test_user.phone_number,
                "password": "test_password"}
        
        response = api_client.post(
            self.endpoint,
            data=data,
            format="json"
        )

        assert response.status_code == 201

        response_data = response.json()
        assert "access_token" in response_data
        assert "refresh_token" in response_data

    def test_view_with_bad_request(self, api_client):
        data = {"username": "test_test",
                "password": "test_password"}
        
        response = api_client.post(
            self.endpoint,
            data=data,
            format="json"
        )

        assert response.status_code == 400

    def test_view_with_not_allowed_method(self, api_client):
        response = api_client.get(
            self.endpoint,
            format="json"
        )

        assert response.status_code == 405


@pytest.mark.django_db
class TestRefreshJWTAPIView:
    @property
    def endpoint(self):
        return reverse("auth:refresh_jwt")
    
    def test_view_with_correct_request(self, api_client, auth_tokens):
        data = {"refresh": auth_tokens["refresh_token"].token}

        response = api_client.post(
            self.endpoint,
            data=data,
            format="json"
        )
            
        assert response.status_code == 201

        response_data = response.json()
        assert "access_token" in response_data

    def test_view_with_bad_request(self, api_client):
        data = {"aaaa": "bbbbbbbbbbbbbbb"}
        
        response = api_client.post(
            self.endpoint,
            data=data,
            format="json"
        )

        assert response.status_code == 400

    def test_view_with_expired_refresh_token(self, api_client, test_user):
        expire_time = timezone.now() - timedelta(hours=1)
        expired_token = RefreshToken.objects.create(user=test_user,
                                                    expires_at=expire_time)
        
        data = {"refresh": str(expired_token.token)}

        response = api_client.post(
            self.endpoint,
            data=data,
            format="json"
        )

        assert response.status_code == 401

        response_data = response.json()
        assert response_data == {"error":
                                 "Время жизни токена истекло. Пройдите процедуру авторизации заново."
                                 }


@pytest.mark.django_db
class TestUserLogoutAPIView:
    @property
    def endpoint(self):
        return reverse("auth:logout")
    
    def test_view_with_correct_request(self, authorized_api_client, auth_tokens):
        response = authorized_api_client.post(
            self.endpoint,
            format="json"
        )
        assert response.status_code == 200

        response_data = response.json()
        assert response_data == {"detail": "Произведен выход из системы"}
        
        assert RefreshToken.objects.get(token=auth_tokens["refresh_token"].token).is_revoked

    def test_view_unauthorized(self, api_client):
        response = api_client.post(
            self.endpoint,
            format="json"
        )

        assert response.status_code == 403

    def test_view_with_incorrect_credentials(self, api_client, auth_tokens):
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {auth_tokens['access_token']}a"
            )
        response = api_client.post(
            self.endpoint,
            format="json"
        )
        assert response.status_code == 403

        errors = response.json()
        assert errors.get("error") == "Неверная сигнатура токена"

        api_client.credentials(
            HTTP_AUTHORIZATION=auth_tokens["access_token"]
            )
        response = api_client.post(
            self.endpoint,
            format="json"
        )
        assert response.status_code == 403
