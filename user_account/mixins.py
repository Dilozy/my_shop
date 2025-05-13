from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator


User = get_user_model()


class URLValidationMixin:
    def _validate_url(self, data):
        user = self.__validate_uidb64(data["uidb64"])
        self.__validate_token(user, data["token"])
        data["user"] = user
        return data

    def __validate_uidb64(self, uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден")
    
    def __validate_token(self, user, token):
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError(
                "Токен некорректен или недействителен"
                )
