from django.urls import path

from . import views


app_name = "orders"

urlpatterns = [
    path("", views.ListCreateOrderAPIView.as_view()),
    path("<uuid:pk>/", views.RetrieveOrderAPIView.as_view(),
         name="retrieve_order"),
]