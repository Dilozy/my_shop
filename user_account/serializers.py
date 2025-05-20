from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

from .services.email_service import EmailService
from .mixins import URLValidationMixin
from authentication.models import RefreshToken


User = get_user_model()


class CreateUserSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True, label="Подтвердите пароль")

    class Meta:
        model = User
        fields = [User.USERNAME_FIELD, *User.REQUIRED_FIELDS,
                  "password", "password_confirm"]
        extra_kwargs = {
            "password": {"write_only": True, "label": "Пароль"}
        }

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
    
        return data

    def save(self):
        self.validated_data.pop("password_confirm", None)
        user = User.objects.create_user(**self.validated_data)
        EmailService.send_activation_email(user)
        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True,
                                             label="Подтвердите пароль",
                                             required=False)
    
    class Meta:
        model = User
        fields = [User.USERNAME_FIELD, *User.REQUIRED_FIELDS,
                  "password", "password_confirm"]
        extra_kwargs = {
            "password": {"write_only": True, "label": "Пароль"}
        }

    def validate(self, data):
        if "password" in data:
            if data.get("password_confirm") is None:
                raise serializers.ValidationError("Необходимо подтвердить пароль")
        
            if data["password"] != data["password_confirm"]:
                raise serializers.ValidationError({"password": "Пароли не совпадают"})
    
        return data

    def update(self, instance, validated_data):
        validated_data.pop("password_confirm", None)
        
        for field, value in validated_data.items():
            if field == "password":
                instance.set_password(value)
            else:
                setattr(instance, field, value)
        
        instance.save()
        return instance
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(self, "validated_data"):
            return self.validated_data
        return data


class RetrieveListUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [User.USERNAME_FIELD, *User.REQUIRED_FIELDS, "is_active"]


class DestroyUserSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        label="Текущий пароль"
    )

    def validate(self, data):
        current_password = data.get("current_password")

        if not check_password(current_password, self.context.get("request").user.password):
            raise serializers.ValidationError({"current_password": "Неверный пароль"})

        return data


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email")

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "Пользователя с таким email не существует"}
                )
        data["user"] = user
        return data
        
    def save(self):
        EmailService.send_reset_password_email(self.validated_data["user"])


class ActivateUserSerializer(serializers.Serializer, URLValidationMixin):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    
    def validate(self, data):
        data = self._validate_url(data)
        if data["user"].is_active:
            raise serializers.ValidationError({"error": "Этот пользователь уже активирован"})
        return data
    
    def save(self):
        user = self.validated_data["user"]
        user.is_active = True
        user.save()
        return user
    
class ResendActivationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Пользователь не найден"})
        
        if user.is_active:
            raise serializers.ValidationError({"email": "Пользователь уже был активирован"})
        data["user"] = user
        return data


class URLValidationSerializer(serializers.Serializer, URLValidationMixin):
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, data):
        return self._validate_url(data)
        
        
class PasswordResetConfirmSerializer(serializers.Serializer, URLValidationMixin):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True,
                                         label="Новый пароль")
    re_new_password = serializers.CharField(write_only=True,
                                            label="Повторите новый пароль")

    def validate(self, data):
        data = self._validate_url(data)

        if data.get("new_password") != data.get("re_new_password"):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        
        return data

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()

        RefreshToken.objects.filter(user=user, is_revoked=False).update(is_revoked=True)

        return user
