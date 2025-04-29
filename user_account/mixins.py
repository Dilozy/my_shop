from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator


User = get_user_model()


class TokenValidationMixin:
    def _validate_token(self, data):
        try:
            print(data)
            uid = force_str(urlsafe_base64_decode(data["uidb64"]))
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            raise serializers.ValidationError("Неверная ссылка активации.")

        if not default_token_generator.check_token(user, data["token"]):
            raise serializers.ValidationError(
                "Срок действия ссылки истёк или она недействительна."
                )

        data["user"] = user
        return data
