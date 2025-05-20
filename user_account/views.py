import requests
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied

from . import serializers
from .services.email_service import EmailService


User = get_user_model()


class ListCreateUsersAPIView(generics.ListCreateAPIView):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.RetrieveListUserSerializer
        return serializers.CreateUserSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Спасибо за регистрацию! Ссылка для активации выслана на почту"},
            status=status.HTTP_201_CREATED
        )


class RetrieveUpdateDestroyUserAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, )

    def get_serializer_class(self):
        if self.request.method == "PUT" or self.request.method == "PATCH":
            return serializers.UpdateUserSerializer
        elif self.request.method == "GET":
            return serializers.RetrieveListUserSerializer
        else:
            return serializers.DestroyUserSerializer

    def get_object(self):
        user = self.request.user
        if not user.is_active:
            raise PermissionDenied("Аккаунт не активирован")
        return user

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            data=request.data, 
            context={"request": request}
            )
        serializer.is_valid(raise_exception=True)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        Token.objects.filter(user=instance).delete()
        instance.delete()


class ActivateUserAPIView(generics.GenericAPIView):
    serializer_class = serializers.ActivateUserSerializer
    
    def get(self, request, uidb64, token):
        try:
            response = requests.patch(
                "http://127.0.0.1:8000" + reverse("users:activate_user"),
                data={"uidb64": uidb64, "token": token},
                timeout=3
            )
            response.raise_for_status()
            return Response(response.json())
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "Ошибка активации", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    def patch(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Аккаунт успешно активирован"})


class ResendActivationEmailAPIView(generics.GenericAPIView):
    serializer_class = serializers.ResendActivationEmailSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        EmailService.send_activation_email(serializer.validated_data["user"])
        return Response(
            {"detail": "Инструкции по активации аккаунта были отправлены на вашу почту"}
            )


class PasswordResetAPIView(generics.GenericAPIView):
    serializer_class = serializers.PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail":"На ваш email высланы дальнейшие указания для сброса пароля"})


class PasswordResetConfirmAPIView(generics.GenericAPIView):
    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.URLValidationSerializer
        return serializers.PasswordResetConfirmSerializer
    
    def get(self, request, uidb64, token):
        data = {"uidb64": uidb64, "token": token}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": "Введите новый пароль"})

    def post(self, request, uidb64, token):
        data = {"uidb64": uidb64, "token": token, **request.data}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True) 
        serializer.save()
        return Response({"detail": "Пароль успешно изменён"},
                        status=status.HTTP_200_OK)
    