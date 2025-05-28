import pytest
from model_bakery import baker
from rest_framework.test import APIRequestFactory

from cart.models import Cart, CartItem
from goods.models import Product


@pytest.fixture
def test_user_cart(test_user):
    cart, _ = Cart.objects.get_or_create(user=test_user)
    
    # Удаляем старые items если есть
    CartItem.objects.filter(cart=cart).delete()
    
    # Создаем новые продукты и items
    products = baker.make(Product, _quantity=10)
    for product in products:
        CartItem.objects.get_or_create(cart=cart, product=product)
    
    return cart


@pytest.fixture
def factory():
    return APIRequestFactory()
