import uuid
from datetime import timedelta

import pytest
from rest_framework.serializers import ValidationError
from django.utils import timezone

from authentication.serializers import CreateJWTSerializer, RefreshJWTSerializer
from authentication.models import RefreshToken
from authentication.services.auth_service import RefreshTokenExpired


@pytest.mark.django_db
class TestCreateJWTSerializer:
    def test_serialized_data(self, test_user):
        user_data = {"username": test_user.phone_number, "password": "test_password"}
        serializer = CreateJWTSerializer(data=user_data)

        assert serializer.is_valid()
        assert serializer.errors == {}

        serialized_data = serializer.save()
        assert len(serialized_data) == 2, "Неверный формат данных, возвращаемых сериализатором"


    def test_serialized_data_with_not_existing_user(self):
        user_data = {"username": "+78888888888", "password": "aabbccdd"}
        serializer = CreateJWTSerializer(data=user_data)

        with pytest.raises(ValidationError, match="Неверный логин или пароль"):
            serializer.is_valid(raise_exception=True)

    def test_serializer_with_bad_request(self):
        user_data = {"aadd": "sdfasdffgasdf", "sddfad": "adfasdfsfd"}

        serializer = CreateJWTSerializer(data=user_data)

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        

@pytest.mark.django_db
class TestRefreshJWTSerializer:
    def test_serialized_data(self, auth_tokens):
        data = {"refresh": auth_tokens["refresh_token"].token}
        serializer = RefreshJWTSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.errors == {}

        serialized_data = serializer.save()
        assert isinstance(serialized_data, str), "Неверный формат данных, возвращаемых сериализатором"
        assert len(serialized_data.split(".")) == 3, "Обновленный токен доступа некорректен"

    def test_serializer_with_non_existing_refresh(self):
        data = {"refresh": str(uuid.uuid4())}
        serializer = RefreshJWTSerializer(data=data)

        with pytest.raises(ValidationError, match="Токен не найден"):
            serializer.is_valid(raise_exception=True)

    def test_serializer_with_expired_refresh_token(self, test_user):
        expire_time = timezone.now() - timedelta(hours=1)
        test_refresh = RefreshToken.objects.create(user=test_user,
                                                   expires_at=expire_time)
        
        data = {"refresh": str(test_refresh.token)}
        serializer = RefreshJWTSerializer(data=data)

        assert serializer.is_valid()

        with pytest.raises(RefreshTokenExpired,
                           match="Время жизни токена истекло. Пройдите процедуру авторизации заново."
                           ):
            serializer.save()

    def test_serializer_with_bad_request(self):
        data = {"aadd": "sdfasdffgasdf"}

        serializer = CreateJWTSerializer(data=data)

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
