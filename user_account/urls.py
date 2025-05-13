from django.urls import path
from django.views.generic import TemplateView

from . import views


app_name = "users"

urlpatterns = [
    path("", views.ListCreateUsersAPIView.as_view(), name="list_create_users"),
    path("activation-confirm/<str:uidb64>/<str:token>/",
         TemplateView.as_view(template_name="activation_confirm.html")),
    path("activate/<str:uidb64>/<str:token>/",
         views.ActivateUserAPIView.as_view(),
         name="user_activation"),
    path("resend-activation/",
         views.ResendActivationEmailAPIView.as_view(),
         name="resend_activation"),
    path("me/",
         views.RetrieveUpdateDestroyUserAPIView.as_view(),
         name="retrieve_update_user"),
    path("reset-password/", views.PasswordResetAPIView.as_view(), name="reset_password"),
    path("reset-password-confirm/<str:uidb64>/<str:token>/",
         views.PasswordResetConfirmAPIView.as_view(),
         name="reset_password_confirm"),
]