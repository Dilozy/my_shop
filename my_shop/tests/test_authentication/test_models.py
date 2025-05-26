import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from authentication.models import RefreshToken


@pytest.mark.django_db
class TestRefreshTokenModel:
    REQUIRED_FIELDS = [field.name for field in RefreshToken._meta.get_fields()]
    
    def test_model_object_has_required_fields(self, auth_tokens):
        refresh_token_obj = auth_tokens["refresh_token"]

        for field in self.REQUIRED_FIELDS:
            assert hasattr(refresh_token_obj, field), f"В объекте модели отсутствует поле {field}"

    def test_model_object_fields_types(self):
        token_field = RefreshToken._meta.get_field("token")
        assert token_field.max_length == 255
        assert token_field.unique
        assert isinstance(token_field.default(), uuid.UUID)

        is_revoked_field = RefreshToken._meta.get_field("is_revoked")
        assert is_revoked_field.default == False

    def test_model_creation(self, test_user):
        test_refresh = RefreshToken.objects.create(user=test_user,
                                                   expires_at=timezone.now() + timedelta(days=7))
        
        for field in self.REQUIRED_FIELDS:
            assert hasattr(test_refresh, field), f"В объекте модели отсутствует поле {field}"

        assert test_refresh.user == test_user, "Владельцы токена не совпадают"

    def test_model_foreign_keys(self, test_user):
        test_user.delete()
        test_user.save()
        assert not RefreshToken.objects.filter(user=test_user).exists(), (
            "Токены не были удалены вместе с пользователем"
            )