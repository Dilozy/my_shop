from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

from .services.email_service import EmailService
from .mixins import TokenValidationMixin


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True, label="Подтвердите пароль")

    class Meta:
        model = User
        fields = [User.USERNAME_FIELD, *User.REQUIRED_FIELDS,
                  "password", "password_confirm", "is_active"]
        read_only_fields = ["is_active"]
        extra_kwargs = {
            "password": {"write_only": True, "label": "Пароль"}
        }

    def validate(self, data):
        user = self.context.get("request").user
        http_method = self.context.get("request").method

        if http_method == "POST":
            if data["password"] != data["password_confirm"]:
                raise serializers.ValidationError("Пароли не совпадают")
        
        if not user.is_active and http_method != "POST":
            raise serializers.ValidationError(
                "Для обновления данных аккаунта необходимо пройти процедуру активации"
            )
        
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        EmailService.send_confirmation_email(user)
        return user
        

class ChangeUserPasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True,
                                         label="Новый пароль")
    re_new_password = serializers.CharField(write_only=True,
                                            label="Повторите новый пароль")
    
    class Meta:
        model = User
        fields = ["password", "new_password", "re_new_password"]
        extra_kwargs = {
            "password": {"write_only": True, "label": "Текущий пароль"}
        }

    def validate(self, data):
        user = self.context.get("request").user
        if not check_password(data.get("password"), user.password):
            raise serializers.ValidationError({"error": "Неверный текущий пароль"})
        
        if data.get("new_password") != data.get("re_new_password"):
            raise serializers.ValidationError({"error": "Пароли не совпадают"})
        
        return data
    
    def create(self, validated_data):
        user = self.context.get("request").user
        user.set_password(validated_data["new_password"])
        user.save()
        return user
    

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            return value
        raise serializers.ValidationError(
            {"error": "Пользователя с таким email не существует"}
            )
    
    def save(self):
        validated_email = self.validated_data["email"]
        user = User.objects.get(email=validated_email)
        EmailService.send_reset_password_email(user)


class ActivateUserSerializer(serializers.Serializer, TokenValidationMixin):
    def validate(self, data):
        return self._validate_token(data)
    
    def save(self):
        user = self.validated_data["user"]
        user.is_active = True
        user.save()
        return user

class TokenValidationSerializer(serializers.Serializer, TokenValidationMixin):
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, data):
        return self._validate_token(data)
        
        
class PasswordResetConfirmSerializer(serializers.Serializer):
    login = serializers.CharField(label="Имя пользователя")
    is_token_valid = serializers.BooleanField()
    new_password = serializers.CharField(write_only=True,
                                         label="Новый пароль")
    re_new_password = serializers.CharField(write_only=True,
                                            label="Повторите новый пароль")

    def validate(self, data):
        if not data.get("is_token_valid"):
            raise serializers.ValidationError({"error": "Передан невалидный токен"})

        if data.get("new_password") != data.get("re_new_password"):
            raise serializers.ValidationError({"error": "Пароли не совпадают"})
        
        user = User.objects.get(phone_number=data["login"])
        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
 



