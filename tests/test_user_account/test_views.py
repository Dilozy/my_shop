from unittest.mock import patch, MagicMock
import time

import pytest
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.hashers import check_password

from user_account import views, serializers
from authentication.models import RefreshToken


User = get_user_model()


@pytest.mark.django_db
class TestListCreateUsersAPIView:
    @property
    def endpoint(self):
        return reverse("users:list_create_users")
    
    @pytest.mark.parametrize("method, expected_serializer", 
        [
            ("get", serializers.RetrieveListUserSerializer),
            ("post", serializers.CreateUserSerializer),
        ]
    )
    def test_get_serializer_class(self, method, expected_serializer):
        view = views.ListCreateUsersAPIView()
        factory = APIRequestFactory()

        request_method = getattr(factory, method)
        request = request_method(self.endpoint, {} if request_method == "post" else None)
        
        view.request = request
        assert view.get_serializer_class() is expected_serializer

    def test_get_method(self, api_client):
        response = api_client.get(self.endpoint)
        assert response.status_code == 200
        
        response_data = response.json()
        assert len(response_data) == 0

    def test_post_method_with_valid_data(self, api_client):
        data = {
            "phone_number": "80000000000",
            "email": "test@test1.com",
            "first_name": "John",
            "last_name": "Smith",
            "password": "12345678",
            "password_confirm": "12345678"
        }

        response = api_client.post(
            self.endpoint,
            data=data,
            format="json"
        )
        assert response.status_code == 201

        response_data = response.json()
        assert response_data.get("detail", []) == "Спасибо за регистрацию! " \
                                                  "Ссылка для активации выслана на почту"

    @pytest.mark.parametrize("data, field, expected_error",[
        (
            {
                "email": "test@test1.com",
                "first_name": "John",
                "last_name": "Smith",
                "password": "12345678",
                "password_confirm": "12345678"
            },
            "phone_number", "This field is required."
        ),
        (
            {
                "phone_number": "80000000000",
                "email": "test@test1.com",
                "first_name": "John",
                "last_name": "Smith",
                "password": "123456789",
                "password_confirm": "12345678"
            },
            "password", "Пароли не совпадают"
        ),
        (
            {
                "phone_number": "+39219773198",
                "email": "test@test1.com",
                "first_name": "John",
                "last_name": "Smith",
                "password": "12345678",
                "password_confirm": "12345678"
            },
            "phone_number",
            "Номер телефона должен быть в формате +79999999999 или 89999999999"
        ),
        (
            {
                "phone_number": "+39219773198",
                "email": "sdfsadfsadfsd",
                "first_name": "John",
                "last_name": "Smith",
                "password": "12345678",
                "password_confirm": "12345678"
            },
            "email",
            "Enter a valid email address."
        )
    ])
    def test_post_method_with_bad_request(self, api_client, data, field, expected_error):
        response = api_client.post(
            self.endpoint,
            data=data,
            format="json"
        )
        assert response.status_code == 400

        errors = response.json()
        assert expected_error in errors.get(field, [])


@pytest.mark.django_db
class TestRetrieveUpdateDestroyUserAPIView:
    @property
    def endpoint(self):
        return reverse("users:me")
    
    @pytest.mark.parametrize("method, expected_serializer",
        [
            ("get", serializers.RetrieveListUserSerializer),
            ("patch", serializers.UpdateUserSerializer),
            ("put", serializers.UpdateUserSerializer),
            ("delete", serializers.DestroyUserSerializer),
        ]
    )
    def test_get_serializer_class(self, method, expected_serializer):
        factory = APIRequestFactory()
        view = views.RetrieveUpdateDestroyUserAPIView()
        
        request_method = getattr(factory, method)
        request = request_method(self.endpoint, {} if method in ("patch", "put") else None)
        
        view.request = request
        assert view.get_serializer_class() is expected_serializer

    def test_get_method(self, test_user, authorized_api_client):
        response = authorized_api_client.get(self.endpoint)
        assert response.status_code == 200

        response_data = response.json()
        expected_fields = ["email", "first_name", "last_name", "phone_number", "is_active"]

        for field in expected_fields:
            assert field in response_data
            assert response_data[field] == getattr(test_user, field)

    def test_put_method_with_valid_data(self, test_user, authorized_api_client):
        data = {
            "email": "test1@test.com",
            "phone_number": "+71112223344",
            "first_name": "tesssst",
            "last_name": "ttttttessst",
            "password": "test_password2",
            "password_confirm": "test_password2"
        }

        response = authorized_api_client.put(
            self.endpoint,
            data=data,
            format="json"
            )
        assert response.status_code == 200
        
        response_data = response.json()
        expected_response_fields = ("first_name", "last_name", "phone_number", "email")
        test_user.refresh_from_db()
        
        for field in expected_response_fields:
            assert data[field] == response_data[field]
            assert data[field] == getattr(test_user, field)

    @pytest.mark.parametrize("data, field, expected_error", [
        (
            {
                "phone_number": "+71112223344",
                "first_name": "tesssst",
                "last_name": "ttttttessst",
                "password": "test_password2",
                "password_confirm": "test_password2"
            },
            "email", "This field is required."
        ),
        (
            {
                "email": "test1@test.com",
                "phone_number": "+71112223344",
                "first_name": "tesssst",
                "last_name": "ttttttessst",
                "password": "test_password2",
                "password_confirm": "test_password3"
            },
            "password", "Пароли не совпадают"
        ),
        (
            {
                "email": "fdsfdsfsd",
                "phone_number": "+71112223344",
                "first_name": "tesssst",
                "last_name": "ttttttessst",
                "password": "test_password2",
                "password_confirm": "test_password2"
            },
            "email",
            "Enter a valid email address."
        ),
        (
            {
                "email": "test1@test.com",
                "phone_number": "+61112223344",
                "first_name": "tesssst",
                "last_name": "ttttttessst",
                "password": "test_password2",
                "password_confirm": "test_password2"
            },
            "phone_number",
            "Номер телефона должен быть в формате +79999999999 или 89999999999"
        )
    ])
    def test_put_with_bad_request(self, authorized_api_client, data, field, expected_error):
        response = authorized_api_client.put(
            self.endpoint,
            data=data,
            format="json"
        )
        assert response.status_code == 400

        errors = response.json()
        assert expected_error in errors.get(field, [])

    def test_delete_method_with_valid_data(self, test_user, authorized_api_client):
        data = {"current_password": "test_password"}
        
        response = authorized_api_client.delete(
            self.endpoint,
            data=data,
            format="json"
        )
        assert response.status_code == 204

        assert not User.objects.filter(pk=test_user.pk).exists()
        assert not RefreshToken.objects.filter(user=test_user).exists()

    @pytest.mark.parametrize("data, field, expected_error", [
        (
            {
                "current_password": "gfdgdfgdfg"
            },
            "current_password",
            "Неверный пароль"
        ),
        (
            {},
            "current_password",
            "This field is required."
        )
    ])
    def test_delete_method_with_bad_request(self, authorized_api_client,
                                            data, field, expected_error):
        response = authorized_api_client.delete(
            self.endpoint,
            data=data,
            format="json"
        )
        assert response.status_code == 400

        errors = response.json()
        assert expected_error in errors.get(field, [])

    def test_patch_method_with_valid_data(self, test_user, authorized_api_client):
        data = {"first_name": "John", "last_name": "Smith"}
        response = authorized_api_client.patch(
            self.endpoint,
            data=data,
            format="json"
        )
        assert response.status_code == 200

        test_user.refresh_from_db()
        response_data = response.json()
        assert data == response_data
        for key, val in data.items():
            assert getattr(test_user, key) == val

    @pytest.mark.parametrize("method_name", [
        "get", "put", "patch", "delete"
    ])
    def test_unauthorized_request(self, api_client, method_name):
        http_method = getattr(api_client, method_name)
        
        if method_name == "get":
            response = http_method(self.endpoint)
        else:
            response = http_method(
                self.endpoint,
                data={},
                format="json"
            )

        assert response.status_code == 403, (
            "Неавторизированный пользователь получил доступ к ресурсу, требующему авторизации"
        )


@pytest.mark.django_db
class TestActivateUserAPIView:
    def get_endpoint(self, activation_credentials):
        return reverse("users:activation_confirm", kwargs=activation_credentials)
    
    def test_get_method(self, api_client, activation_credentials):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"detail": "Аккаунт успешно активирован"}
        mock_response.raise_for_status.return_value = None

        with patch("user_account.views.requests.patch", return_value=mock_response) as mock_patch:
            response = api_client.get(self.get_endpoint(activation_credentials))

            mock_patch.return_value = mock_response
        
            response = api_client.get(
                self.get_endpoint(activation_credentials),
            )
            assert response.status_code == 200

            response_data = response.json()
            assert response_data.get("detail") == "Аккаунт успешно активирован"

    def test_patch_method_with_valid_data(self, api_client, test_user_not_activated,
                                          activation_credentials):
        response = api_client.patch(
            reverse("users:activate_user"),
            data=activation_credentials,
            format="json"
            )
        assert response.status_code == 200

        response_data = response.json()
        assert response_data.get("detail") == "Аккаунт успешно активирован"
        test_user_not_activated.refresh_from_db()
        assert test_user_not_activated.is_active
    
    @pytest.mark.parametrize("get_data, field, expected_error", [
        (
            lambda ac: {
                "uidb64": urlsafe_base64_encode(force_bytes(100_000_000)),
                "token": ac["token"]
            },
            "uidb64", "Пользователь не найден"
        ),
        (
            lambda ac: {
                "uidb64": ac["uidb64"],
                "token": ac["token"] + "fff"
            },
            "token", "Токен некорректен или недействителен"
        )
    ])
    def test_patch_method_with_bad_request(self, api_client, test_user_not_activated,
                                           activation_credentials, get_data, field,
                                           expected_error):
        data = get_data(activation_credentials)
        response = api_client.patch(
            reverse("users:activate_user"),
            data=data,
            format="json"
        )
        assert response.status_code == 400

        errors = response.json()
        assert expected_error in errors.get(field, [])
        test_user_not_activated.refresh_from_db()
        assert not test_user_not_activated.is_active
    
    def test_activation_flow(self, api_client, test_user_not_activated,
                             activation_credentials):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_client.patch(
            reverse("users:activate_user"),
            data=activation_credentials,
            format="json"
        ).json()
        mock_response.raise_for_status.return_value = None
        
        with patch("user_account.views.requests.patch", return_value=mock_response) as mock_patch:
            response = api_client.get(self.get_endpoint(activation_credentials))

            assert response.status_code == 200
            assert response.json()["detail"] == "Аккаунт успешно активирован"
            
            test_user_not_activated.refresh_from_db()
            assert test_user_not_activated.is_active
            
            mock_patch.assert_called_once()


@pytest.mark.django_db
class TestResendActivationEmailAPIView:
    @property
    def endpoint(self):
        return reverse("users:resend_activation")
    
    def test_view_with_valid_data(self, api_client, test_user_not_activated):
        data = {"email": test_user_not_activated.email}
        with patch("user_account.services.email_service.send_mail") as mock_send:
            response = api_client.post(
                self.endpoint,
                data=data,
                format="json"
            )
            time.sleep(.1)
            assert response.status_code == 200
            mock_send.assert_called_once()

            response_data = response.json()
            assert response_data["detail"] == "Инструкции по активации аккаунта были отправлены на вашу почту"

    @pytest.mark.parametrize("data, expected_error", [
        (
            {
                "email": "test@gmail.com"
            },
            "Пользователь уже был активирован"
        ),
        (
            {
                "email": "fssdfdsf@dsfdsf.com"
            },
            "Пользователь не найден"
        )
    ])
    def test_view_with_bad_request(self, api_client, data, expected_error, test_user):
        with patch("user_account.services.email_service.send_mail") as mock_send:
            response = api_client.post(
                self.endpoint,
                data=data,
                format="json"
            )
            assert response.status_code == 400

            errors = response.json()
            assert expected_error in errors.get("email", [])
            mock_send.assert_not_called()


@pytest.mark.django_db
class TestPasswordResetAPIView:
    @property
    def endpoint(self):
        return reverse("users:reset_password")
    
    def test_view_with_valid_data(self, api_client, test_user):
        data = {"email": test_user.email}
        with patch("user_account.services.email_service.send_mail") as mock_send:
            response = api_client.post(
                self.endpoint,
                data=data,
                format="json"
            )
            time.sleep(.1)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["detail"] == "На ваш email высланы дальнейшие указания для сброса пароля"
            mock_send.assert_called_once()

    def test_view_with_bad_request(self, api_client):
        data = {"email": "invalid_email@test.com"}
        with patch("user_account.services.email_service.send_mail") as mock_send:
            response = api_client.post(
                self.endpoint,
                data=data,
                format="json"
            )
            assert response.status_code == 400

            errors = response.json()
            assert "Пользователя с таким email не существует" in errors.get("email", [])
            mock_send.assert_not_called()


@pytest.mark.django_db
class TestPasswordResetConfirmAPIView:
    def get_endpoint(self, reset_credentials):
        return reverse("users:reset_password_confirm", kwargs=reset_credentials)
    
    @pytest.mark.parametrize("method, expected_serializer", [
        ("get", serializers.URLValidationSerializer),
        ("post", serializers.PasswordResetConfirmSerializer)
    ])
    def test_get_serializer_class(self, method, expected_serializer, reset_credentials):
        view = views.PasswordResetConfirmAPIView()
        factory = APIRequestFactory()

        http_method = getattr(factory, method)
        request = http_method(self.get_endpoint(reset_credentials), {} if method == "post" else None)
        
        view.request = request
        assert view.get_serializer_class() is expected_serializer
    
    @pytest.mark.parametrize("get_data, field, expected_error", [
        (
            lambda rc: {
                "uidb64": urlsafe_base64_encode(force_bytes(100_000_000)),
                "token": rc["token"]
            },
            "uidb64", "Пользователь не найден"
        ),
        (
            lambda rc: {
                "uidb64": rc["uidb64"],
                "token": rc["token"] + "fff"
            },
            "token", "Токен некорректен или недействителен"
        )
    ])
    def test_get_method_with_bad_request(self, api_client, reset_credentials, get_data,
                                         field, expected_error):
        invalid_credentials = get_data(reset_credentials)
        response = api_client.get(self.get_endpoint(invalid_credentials))
        assert response.status_code == 400

        errors = response.json()
        assert expected_error in errors.get(field, [])

    def test_get_method_with_valid_data(self, api_client, reset_credentials):
        response = api_client.get(self.get_endpoint(reset_credentials))
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["detail"] == "Введите новый пароль"

    def test_post_method_with_valid_data(self, api_client, reset_credentials, test_user):
        data = {"new_password": "test_password1",
                "re_new_password": "test_password1",
                }
        response = api_client.post(
            self.get_endpoint(reset_credentials),
            data=data,
            format="json"
        )
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["detail"] == "Пароль успешно изменён"
        test_user.refresh_from_db()
        assert check_password("test_password1", test_user.password)
        assert not RefreshToken.objects.filter(user=test_user, is_revoked=False).exists()

    @pytest.mark.parametrize("get_data, field, expected_error", [
        (
            lambda rc: {
                "uidb64": urlsafe_base64_encode(force_bytes(100_000_000)),
                "token": rc["token"],
                "new_password": "test_password1",
                "re_new_password": "test_password1"
            },
            "uidb64", "Пользователь не найден"
        ),
        (
            lambda rc: {
                "uidb64": rc["uidb64"],
                "token": rc["token"] + "fff",
                "new_password": "test_password1",
                "re_new_password": "test_password1"
            },
            "token", "Токен некорректен или недействителен"
        ),
        (
            lambda rc: {
                "uidb64": rc["uidb64"],
                "token": rc["token"],
                "new_password": "test_password1",
                "re_new_password": "test_password2"
            },
            "password", "Пароли не совпадают"
        ),
        (
            lambda rc: {
                "uidb64": rc["uidb64"],
                "token": rc["token"],
                "new_password": "test_password1",
            },
            "re_new_password", "This field is required.")
    ])
    def test_post_method_with_bad_request(self, test_user, api_client, reset_credentials,
                                          get_data, field, expected_error):
        response = api_client.post(
            self.get_endpoint(reset_credentials),
            data=get_data(reset_credentials),
            format="json"
        )
        assert response.status_code == 400

        errors = response.json()
        assert expected_error in errors.get(field, [])
        assert not check_password("test_password1", test_user.password)
