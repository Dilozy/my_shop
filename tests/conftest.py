import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


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