import pytest
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from model_bakery import baker

from cart.models import Cart
from cart.services import get_or_create_cart, add_item_to_cart
from goods.models import Product


@pytest.mark.django_db
class TestGetOrCreateCart:
    @property
    def endpoint(self):
        return reverse("cart:my_cart")

    def test_service_for_not_authenticated_user(self, factory):
        request = factory.get(self.endpoint)
        user = AnonymousUser()

        assert "cart_id" not in request.COOKIES
        cart = get_or_create_cart(user, request.COOKIES)
        assert Cart.objects.filter(pk=cart.cart_id).exists()
        
        request.COOKIES["cart_id"] = str(cart.cart_id)
        another_cart = get_or_create_cart(user, request.COOKIES)
        assert cart == another_cart

    def test_service_for_autenticated_user(self, test_user, test_user_cart, authorized_api_client):
        response = authorized_api_client.get(
            self.endpoint
        )
        request = response.wsgi_request
        assert not response.cookies["cart_id"].value

        cart = get_or_create_cart(test_user, request.COOKIES)
        assert cart == test_user_cart

    def test_service_for_autenticated_user_without_cart(self, test_user, factory):
        Cart.objects.filter(user=test_user).delete()
        request = factory.get(
            self.endpoint
        )
        assert not Cart.objects.filter(user=test_user).exists()

        cart = get_or_create_cart(test_user, request.COOKIES)
        assert cart == Cart.objects.get(user=test_user)


@pytest.mark.django_db
class TestAddItemToCart:
    def test_add_new_item_to_cart(self, test_user_cart):
        products = baker.make(
            Product,
            _quantity=1
        )

        cart_item = add_item_to_cart(test_user_cart, products[0])
        assert cart_item.cart == test_user_cart
        assert cart_item.quantity == 1

    def test_increase_item_quantity_in_the_cart(self, test_user_cart):
        item = test_user_cart.items.first()
        
        cart_item = add_item_to_cart(test_user_cart, item.product)
        assert cart_item.cart == test_user_cart
        assert cart_item.quantity == 2