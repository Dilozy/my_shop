from django.urls import path

from . import views


app_name = "cart"

urlpatterns = [
    path("my-cart/", views.CartAPIView.as_view(), name="my_cart"),
    path("my-cart/items/<int:pk>/", views.CartItemAPIView.as_view(), name="update_cart_item"),
    path("my-cart/items/", views.CartItemAPIView.as_view(), name="cart_items"),
]