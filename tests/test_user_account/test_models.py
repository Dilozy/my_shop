import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from user_account.models import User
from user_account.manager import UserManager


@pytest.mark.django_db
class TestUserModel:
    def test_default_user_model(self, test_user):
        user_model = get_user_model()
        assert isinstance(test_user, user_model)

    def test_model_fields_types(self):
        phone_number_field = User._meta.get_field("phone_number")
        assert phone_number_field.unique
        assert phone_number_field.max_length == 12
        assert phone_number_field.verbose_name == "Номер телефона"

        first_name_field = User._meta.get_field("first_name")
        assert first_name_field.max_length == 50
        assert first_name_field.verbose_name == "Имя"

        last_name_field = User._meta.get_field("last_name")
        assert last_name_field.max_length == 50
        assert last_name_field.verbose_name == "Фамилия"

        is_active_field = User._meta.get_field("is_active")
        assert is_active_field.default == False
        assert is_active_field.verbose_name == "Аккаунт подтвержден"

        is_admin_field = User._meta.get_field("is_admin")
        assert is_admin_field.default == False
        assert is_admin_field.verbose_name == "Администратор"

        email_field = User._meta.get_field("email")
        assert email_field.max_length == 255
        assert email_field.verbose_name == "E-mail"

    def test_required_fields(self):
        assert User.REQUIRED_FIELDS == ["first_name", "last_name", "email"]
        assert User.USERNAME_FIELD == "phone_number"

    def test_default_model_manager(self):
        assert isinstance(User.objects, UserManager)

    def test_str_method(self, test_user):
        assert isinstance(test_user.__str__(), str)
        assert test_user.__str__() == test_user.email
        
    def test_model_properties(self, test_user):
        assert test_user.username == test_user.phone_number
        assert test_user.is_staff == test_user.is_admin

    def test_model_additional_methods(self, test_user):
        assert test_user.get_full_name() == f"{test_user.first_name} {test_user.last_name}"
        assert test_user.get_short_name() == test_user.first_name

    def test_model_phone_regex_validator(self):
        invalid_numbers = ("+69211113055", "fffffff", "79215553456", "+89219334055")
        
        for number in invalid_numbers:
            invalid_user = User.objects.create(
                phone_number=number,
                is_active=True,
                first_name="test",
                last_name="test",
                email="test@gmail.com"
                )
            invalid_user.set_password("test_pasword")
            
            with pytest.raises(ValidationError):
                invalid_user.full_clean()
