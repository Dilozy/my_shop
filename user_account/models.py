from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator

from .manager import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, verbose_name="E-mail")
    phone_regex = RegexValidator(regex=r"^((\+7)|8)\d{10}$",
                                 message="Номер телефона должен быть в формате +79999999999 или /"
                                 "89999999999")
    phone_number = models.CharField(validators=[phone_regex],
                                    max_length=12,
                                    unique=True,
                                    verbose_name="Номер телефона")
    first_name = models.CharField(max_length=50,
                                  verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    is_active = models.BooleanField(default=False, verbose_name="Аккаунт подтвержден")
    is_admin = models.BooleanField(default=False, verbose_name="Администратор")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    
    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["first_name", "last_name", "email"]

    objects = UserManager()

    def __str__(self) -> str:
        return self.email

    @property
    def is_staff(self):
        return self.is_admin    
    
    @property
    def username(self):
        return self.get_full_name()
    
    def get_full_name(self):
        return f"{self.last_name} {self.first_name}"
    
    def get_short_name(self):
        return self.first_name
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
