from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.views import APIView
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

    def perform_destroy(self, instance):
        Token.objects.filter(user=instance).delete()
        instance.delete()


class ActivateUserAPIView(APIView):
    def patch(self, request, uidb64, token):
        serializer = serializers.ActivateUserSerializer(data={"uidb64": uidb64,
                                                              "token": token})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Аккаунт успешно активирован"})


class ResendActivationEmailAPIView(APIView):
    def post(self, request):
        user = request.user
        
        if not user.is_active:
            EmailService.send_confirmation_email(user)
            return Response({"detail": "Email для активации аккаунта был отправлен на вашу почту"})
        else:
            return Response({"error": "Аккаунт пользователя уже активирован"},
                            status=status.HTTP_400_BAD_REQUEST)


class PasswordResetAPIView(generics.GenericAPIView):
    serializer_class = serializers.PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail":"На ваш email высланы дальнейшие указания для сброса пароля"})
    

class PasswordResetTokenVerifyAPIView(APIView):
    def get(self, request, uidb64, token):
        serializer = serializers.TokenValidationSerializer(data={"uidb64": uidb64,
                                                                 "token": token})
        
        if not serializer.is_valid():
            return Response(
                {"valid": False, "error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response({
            "valid": True,
            "user": serializer.validated_data["user"].phone_number
        })
    

class PasswordResetConfirmAPIView(generics.GenericAPIView):
    serializer_class = serializers.PasswordResetConfirmSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Пароль успешно изменён"},
                        status=status.HTTP_200_OK)
