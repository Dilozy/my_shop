from random import randint

import pytest
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from model_bakery import baker

from unittest.mock import patch

from user_account.services.email_service import EmailService


User = get_user_model()


@pytest.mark.django_db
class TestEmailService:
    @pytest.fixture
    def url(self, test_user):
        base_url = "http://example.com/activate/"
        url = EmailService._create_url(test_user, base_url)

        formatted_url = url.rstrip("/").split("/")
        uidb64, token = formatted_url[-2], formatted_url[-1]
        uid = force_str(urlsafe_base64_decode(uidb64))
        
        return {"uid": uid, "token": token, "url": url}
    
    @pytest.fixture
    def test_users(self):
        def generate_phone():
            return f"+79{randint(100000000, 999999999)}"

        return baker.make(
            User,
            is_active=False,
            phone_number=generate_phone,
            _quantity=40
        )

    def test_activation_credentials(self, test_user, url):
        user = User.objects.filter(pk=url["uid"]).first()
        assert user, "Пользователь был не найден"
        assert user == test_user, "Пользователи не совпадают"
        assert default_token_generator.check_token(user, url["token"]), "Неверный токен"

    def test_send_activation_message(self, test_user, url):
        fake_html_message = render_to_string(
            "activation_email.html",
            {
                "user": test_user,
                "activation_url": url["url"]
            }
        )

        with patch("user_account.services.email_service.EmailService._create_url", return_value=url["url"]), \
            patch("user_account.services.email_service.render_to_string", return_value=fake_html_message), \
            patch("user_account.services.email_service.send_mail") as mock_send_mail:

            future = EmailService.send_activation_email(test_user)
            future.result()

            mock_send_mail.assert_called_once_with(
                subject="Активация нового аккаунта",
                message="",
                from_email=None,
                recipient_list=[test_user.email],
                html_message=fake_html_message,
                fail_silently=False,
            )

    def test_many_activation_emails(self, test_users):
        with patch("user_account.services.email_service.send_mail") as mock_send_mail:
            [EmailService.send_activation_email(user).result() for user in test_users]

            assert mock_send_mail.call_count == 40

    def test_send_activation_email_with_non_existant_template(self, test_user):
        with patch("user_account.services.email_service.render_to_string",
                   side_effect=TemplateDoesNotExist("activation_email.html")):
            with pytest.raises(TemplateDoesNotExist):
                EmailService.send_activation_email(test_user)
            
    def test_send_reset_password_email(self, test_user, url):
        fake_html_message = render_to_string(
            "reset_password_email.html",
            {"user": test_user, "reset_url": url["url"]}
        )
        with patch("user_account.services.email_service.EmailService._create_url", return_value=url["url"]), \
            patch("user_account.services.email_service.render_to_string", return_value=fake_html_message), \
            patch("user_account.services.email_service.send_mail") as mock_send_mail:

            future = EmailService.send_reset_password_email(test_user)
            future.result()

            mock_send_mail.assert_called_once_with(
                subject="Сброс пароля",
                message="",
                from_email=None,
                recipient_list=[test_user.email],
                html_message=fake_html_message,
                fail_silently=False
            )

    def test_many_reset_password_emails(self, test_users):
        with patch("user_account.services.email_service.send_mail") as mock_send:
            [EmailService.send_reset_password_email(user).result() for user in test_users]

            assert mock_send.call_count == 40, (
                "Количество отправленных писем не совпадает с количеством пользователей"
            )
        
    def test_send_reset_password_email_with_non_existant_template(self, test_user):
        with patch("user_account.services.email_service.render_to_string",
                   side_effect=TemplateDoesNotExist("reset_password_email.html")):
            with pytest.raises(TemplateDoesNotExist):
                EmailService.send_activation_email(test_user)
