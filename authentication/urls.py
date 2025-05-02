from django.urls import path

from . import views


app_name = "auth"

urlpatterns = [
    path("logout/", views.UserLogoutAPIView.as_view(), name="logout"),
    path("token/refresh/", views.RefreshJWTAPIView.as_view(), name="refresh_jwt"),
    path("token/", views.CreateJWTAPIView.as_view(), name="obtain_jwt"),
]
