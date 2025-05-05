from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

from .services.email_service import EmailService
from .mixins import TokenValidationMixin


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
        if data.get("password_confirm") is None:
            raise serializers.ValidationError("Необходимо подтвердить пароль")
        
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Пароли не совпадают")
    
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
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
                    raise serializers.ValidationError("Пароли не совпадают")
    
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
        
        if not current_password:
            raise serializers.ValidationError({"error": "Необходимо ввести пароль"})
        
        if not check_password(current_password, self.context.get("request").user.password):
            raise serializers.ValidationError({"error": "Неверный пароль"})

        return data


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
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    
    def validate(self, data):
        print(data)
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
 



