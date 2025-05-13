from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.serializers import ValidationError

from user_account import serializers as user_serializers
from user_account.services.email_service import EmailService


User = get_user_model()


@pytest.mark.django_db
class TestCreateUserSerializer:
    def test_serialized_data(self, test_user):
        data = {"phone_number": "+79318807891",
                "first_name": test_user.first_name,
                "last_name": test_user.last_name,
                "email": test_user.email,
                "password": "test_password",
                "password_confirm": "test_password"}
        
        serializer = user_serializers.CreateUserSerializer(data=data)
        assert serializer.is_valid(), "Сериализатору были передеаны некорректные данные"

        created_user = serializer.save()
        assert isinstance(created_user, User), "Сериализатор вернул неверный объект"
        assert not created_user.is_active
        assert not created_user.is_staff
        assert not created_user.is_superuser

    @pytest.mark.parametrize("data, expected_error", [
        (
            {
                "phone_number": "+79318807892",
                "first_name": "John",
                "last_name": "Smith",
                "email": "JohnSmith@test.com",
                "password": "test_password",
                "password_confirm": "test_password11"
            },
            "Пароли не совпадают"
        ),
        (
            {
                "phone_number": "+79318807892",
                "first_name": "John",
                "last_name": "Smith",
                "email": "JohnSmith@test.com",
                "password": "test_password",
                # password_confirm отсутствует
            },
            "This field is required"
        ),
        (
            {
                "phone_number": "+79318807892",
                "first_name": "John",
                "last_name": "Smith",
                "email": "asdfasdfs",
                "password": "test_password",
                "password_confirm": "test_password"
            },
            "Enter a valid email address."
        ),
    ])
    def test_serializer_with_incorrect_data(self, data, expected_error):
        serializer = user_serializers.CreateUserSerializer(data=data)
        with pytest.raises(ValidationError, match=expected_error):
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestUpdateUserSerializer:
    @pytest.mark.parametrize("data", [
        (
            {
                "phone_number": "+70000000000",
                "first_name": "John",
                "last_name": "Smith",
                "email": "JonhSmith@test.com",
                "password": "test_password1",
                "password_confirm": "test_password1"
            }
        )
    ])
    def test_full_object_update(self, test_user, data):
        serializer = user_serializers.UpdateUserSerializer(instance=test_user, data=data)
        assert serializer.is_valid()
        
        updated_user = serializer.save()
        for field, value in data.items():
            if not "password" in field:
                assert getattr(updated_user, field) == value
    
    @pytest.mark.parametrize("data", [
        (
            {
                "password": "test_password1",
                "password_confirm": "test_password1"
            }
        ),
        (
            {
                "email": "JohnSmith@test.com"
            }
        ),
        (
            {
                "first_name": "Joe",
                "last_name": "Foster"
            }
        ),
        (
            {}
        )
    ])
    def test_partial_object_update(self, test_user, data):
        serializer = user_serializers.UpdateUserSerializer(instance=test_user,
                                                           data=data,
                                                           partial=True)
        
        assert serializer.is_valid(raise_exception=True)

        updated_user = serializer.save()
        for field, value in data.items():
            if not "password" in field:
                assert getattr(updated_user, field) == value

    @pytest.mark.parametrize("data, expected_error", [
        (
            {
                "password": "aabbccddff"
            },
            "Необходимо подтвердить пароль"
        ),
        (
            {
                "password": "test_password2",
                "password_confirm": "test_password3"
            },
            "Пароли не совпадают"
        )
    ])
    def test_update_password(self, test_user, data, expected_error):
        serializer = user_serializers.UpdateUserSerializer(instance=test_user,
                                                           data=data,
                                                           partial=True)
        
        with pytest.raises(ValidationError, match=expected_error):
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestRetrieveListUserSerializer:
    def test_serialized_data(self, test_user):
        serializer = user_serializers.RetrieveListUserSerializer(test_user)
        data = serializer.data

        assert set(data.keys()) == {"email", "first_name", "last_name", "is_active", "phone_number"}
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
        assert data["is_active"] == test_user.is_active
        assert data["phone_number"] == test_user.phone_number


@pytest.mark.django_db
class TestDestroyUserSerializer:
    @pytest.fixture
    def mock_request(self, test_user):
        mock_request = Mock()
        mock_request.user = test_user
        return mock_request

    def test_serializer_with_valid_data(self, mock_request):
        data = {"current_password": "test_password"}
        serializer = user_serializers.DestroyUserSerializer(data=data,
                                                            context={"request": mock_request})
        
        assert serializer.is_valid()
        
    @pytest.mark.parametrize("data, expected_error", [
        (
            {
                "current_password": "aabbccddff"
            },
            "Неверный пароль"
        ),
        (
            {},
            "This field is required."
        )
    ])
    def test_serializer_with_invalid_data(self, mock_request, data, expected_error):
        serializer = user_serializers.DestroyUserSerializer(data=data,
                                                            context={"request": mock_request})
        
        with pytest.raises(ValidationError, match=expected_error):
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestPasswordResetSerializer:
    def test_serializer_with_valid_data(self, test_user):
        data = {"email": test_user.email}
        serializer = user_serializers.PasswordResetSerializer(data=data)

        assert serializer.is_valid()

    @pytest.mark.parametrize("data, expected_error", [
        (
            {
                "email": "SmithJohn@test.com"
            },
            "Пользователя с таким email не существует"
        ),
        (
            {
                "email": "sdfsdfsdsdfs"
            },
            "Enter a valid email address."
        )
    ])
    def test_serializer_with_invalid_data(self, data, expected_error):
        serializer = user_serializers.PasswordResetSerializer(data=data)
        with pytest.raises(ValidationError, match=expected_error):
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestActivateUserSerializer:
    @property
    def base_endpoint(self):
        return "http://127.0.0.1:8000/api/v1/users/activation-confirm/"
    
    @pytest.fixture
    def test_user_not_activated(self):
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
    def activation_credentials(self, test_user_not_activated):
        endpoint = EmailService._create_url(test_user_not_activated, self.base_endpoint) \
                               .rstrip("/").split("/")
        
        return {"uidb64": endpoint[-2], "token": endpoint[-1]}

    def test_serializer_with_valid_data(self, activation_credentials):
        serializer = user_serializers.ActivateUserSerializer(data=activation_credentials)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.is_active, "Пользователь не был активирован"

    @pytest.mark.parametrize("get_data, expected_error",[
        (
            lambda ac: {"uidb64": urlsafe_base64_encode(force_bytes(2000))},
            "This field is required",
        ),
        (
            lambda ac: {
                "uidb64": ac["uidb64"],
                "token": ac["token"] + "a",
            },
            "Токен некорректен или недействителен",
        ),
        (
            lambda ac: {
                "uidb64": urlsafe_base64_encode(force_bytes("10_000_000")),
                "token": ac["token"],
            },
            "Пользователь не найден",
        )
    ])
    def test_serializer_with_invalid_data(self, get_data, expected_error, activation_credentials):
        # это lambda, принимающая activation_credentials, чтобы можно было использовать его внутри параметров.
        data = get_data(activation_credentials)
        serializer = user_serializers.ActivateUserSerializer(data=data)

        with pytest.raises(ValidationError, match=expected_error):
            serializer.is_valid(raise_exception=True)
