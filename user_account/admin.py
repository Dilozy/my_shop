from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User


class MyUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].label = "Пароль"


class MyUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Новый пароль"
        self.fields["password1"].help_text = "Ваш пароль не должен быть слишком похож на вашу другую личную информацию.\n"\
                                             "Ваш пароль должен содержать не менее 8 символов.\n"\
                                             "Ваш пароль не может быть общеупотребимым паролем.\n"\
                                             "Ваш пароль не может состоять только из цифр."
        self.fields["password2"].label = "Повторите пароль"
        self.fields["password2"].help_text = "Введите тот же пароль, что и раньше, для проверки."


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = MyUserChangeForm
    add_form = MyUserCreationForm

    empty_value_display = "-empty-"
    list_display = ["phone_number", "email"]
    list_filter = ["is_admin"]
    readonly_fields = ["date_joined"]
    search_fields = ["phone_number"]

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "first_name", "last_name", "email", "password1", "password2"),
        }),
    )

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Личная информация", {"fields": ("first_name", "last_name", "email")}),
        ("Разрешения", {"fields": ("is_active", "is_admin")}),
        ("Важные даты", {"fields": ("date_joined", )}),
    )

    ordering = ["email"]
