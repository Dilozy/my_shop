import pytest
from django.contrib.auth import get_user_model

from user_account.services.email_service import EmailService

User = get_user_model()


@pytest.fixture
def test_user_not_activated():
    user = User.objects.create(
        email="JohnSmith@test.com",
        phone_number="+75555555555",
        first_name="John",
        last_name="Smith"
    )
    user.set_password("test_password")
    user.save()
    return user


@pytest.fixture
def activation_credentials(test_user_not_activated):
    base_endpoint = "http://127.0.0.1:8000/api/v1/users/activation-confirm/"
    endpoint = EmailService._create_url(test_user_not_activated, base_endpoint) \
                            .rstrip("/").split("/")
    
    return {"uidb64": endpoint[-2], "token": endpoint[-1]}


@pytest.fixture
def reset_credentials(test_user):
    base_endpoint = "http://127.0.0.1:8000/api/v1/users/reset-password-confirm/"
    endpoint = EmailService._create_url(test_user, base_endpoint) \
                            .rstrip("/").split("/")
    
    return {"uidb64": endpoint[-2], "token": endpoint[-1]}