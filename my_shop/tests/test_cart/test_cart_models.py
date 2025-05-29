import pytest
from model_bakery import baker
from django.contrib.auth import get_user_model

from goods.models import Product
from cart.models import Cart, CartItem


User = get_user_model()


@pytest.mark.django_db
class TestCartModel:
    @pytest.fixture
    def test_products(self):
        return baker.make(
            Product,
            _quantity=2,
            price=100
        )
    
    @pytest.fixture
    def test_cart(self, test_user):
        return Cart.objects.create(user=test_user)
    
    def test_total_price_property(self, test_products, test_cart):
        for product in test_products:
            CartItem.objects.create(cart=test_cart, product=product)
        
        assert test_cart.total_price == 200

    def test_user_fields(self, test_cart, test_user):
        assert isinstance(test_cart.user, User)
        assert test_cart.user == test_user
        assert test_user.cart == test_cart

        test_user.delete()
        assert not Cart.objects.filter(pk=test_cart.pk).exists()
