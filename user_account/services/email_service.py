from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth import get_user_model


User = get_user_model()


class EmailService:
    _executor = ThreadPoolExecutor(max_workers=10)

    @staticmethod
    def _create_url(user, base_url):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        return base_url + f"{uid}/{token}/"
    
    @staticmethod
    def send_confirmation_email(user):
        endpoint = "http://127.0.0.1:8000/users/activation-confirm/"
        confirmation_url = EmailService._create_url(user, endpoint)
        subject = "Активация нового аккаунта"
        html_message = render_to_string(
            "confirmation_email.html",
            {"user": user, "confirmation_url": confirmation_url}
        )

        EmailService._executor.submit(
            send_mail,
            subject=subject,
            message="",
            from_email=None,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )

    @staticmethod
    def send_reset_password_email(user):
        endpoint = "http://127.0.0.1:8000/users/reset-password-token-verify/"
        reset_url = EmailService._create_url(user, endpoint)
        subject = "Сброс пароля"
        html_message = render_to_string(
            "reset_password_email.html",
            {"user": user, "reset_url": reset_url}
        )

        EmailService._executor.submit(
            send_mail,
            subject=subject,
            message="",
            from_email=None,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
