import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from authentication.models import RefreshToken


User = get_user_model()


@pytest.fixture
def test_user():
    user = User.objects.create(
        phone_number="+71112223344",
        is_active=True,
        first_name="test",
        last_name="test",
        email="test@gmail.com"
        )
    user.set_password("test_password")
    user.save()
    return user


@pytest.fixture()
def auth_tokens(api_client, test_user):
    credentials = {
        "username": test_user.phone_number,
        "password": "test_password"
    }
    
    response = api_client.post(
        reverse("auth:obtain_jwt"),
        data=credentials,
        format="json"
    )
    
    assert response.status_code == 201, (
        f"Ошибка аутентификации. Ответ: {response.json()}"
    )
    
    response_data = response.json()
    response_data["refresh_token"] = RefreshToken.objects.get(token=response_data["refresh_token"])
    
    return response_data

@pytest.fixture
def authorized_api_client(api_client, auth_tokens):
    """
    Возвращает api_client с установленным access-токеном.
    """
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {auth_tokens['access_token']}"
    )
    return api_client
