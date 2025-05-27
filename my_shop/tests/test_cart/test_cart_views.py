from unittest.mock import patch

import pytest
from model_bakery import baker
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model

from cart import views
from cart.models import Cart, CartItem
from cart.serializers import (
    CartSerializer, CartAddItemSerializer, CartReduceItemQuantitySerializer
)
from goods.models import Product


User = get_user_model()


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.mark.django_db
class TestCartAPIView:
    @property
    def endpoint(self):
        return reverse("cart:my_cart")
    
    def test_get_object_with_a_new_cart(self, factory, test_user):
        view = views.CartAPIView()

        request = factory.get(self.endpoint)
        request.user = test_user
        view.request = request
        
        retrieved_cart = view.get_object()
        assert retrieved_cart.user == test_user

    def test_get_object_with_existing_cart(self, factory, test_user):
        cart = Cart.objects.create(user=test_user)
        
        view = views.CartAPIView()

        request = factory.get(self.endpoint)
        request.user = test_user
        view.request = request
        
        retrieved_cart = view.get_object()
        assert retrieved_cart == cart

    def test_get_method_with_authorized_user(self, test_user_cart,
                                             authorized_api_client):
        response = authorized_api_client.get(
            self.endpoint
        )
        assert response.status_code == 200

        response_data = response.json()
        assert response_data.get("items") is not None, "Эндпоинт вернул пустой ответ"
        assert len(response_data["items"]) == 10
        serializer = CartSerializer(test_user_cart)
        assert serializer.data["items"] == response_data["items"]

    def test_get_method_with_unathorized_user(self, api_client):
        response = api_client.get(
            self.endpoint
        )
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["detail"] == "Ваша корзина пуста"
        assert Cart.objects.filter(pk=response.cookies["cart_id"].value).exists()
    
    def test_delete_method_with_authorized_user(self, test_user_cart,
                                                authorized_api_client, test_user):
        response = authorized_api_client.delete(
            self.endpoint
        )
        assert response.status_code == 200

        response_data = response.json()
        assert response_data.get("detail") == "Корзина очищена"
        
        test_user_cart.refresh_from_db()
        assert len(test_user_cart.items.all()) == 0
        assert Cart.objects.filter(user=test_user).exists()

    def test_delete_method_with_unauthorized_user(self, api_client):
        response = api_client.get(
            self.endpoint
        )
        cart_id = response.cookies["cart_id"].value
        api_client.cookies["cart_id"] = cart_id

        delete_response = api_client.delete(
            self.endpoint
        )
        assert delete_response.status_code == 200
        
        delete_response_data = delete_response.json()
        assert delete_response_data["detail"] == "Корзина очищена"

        assert not Cart.objects.filter(pk=cart_id).exists(), "Корзина не была удалена"

    def test_cart_with_incorrect_user(self, authorized_api_client):

        new_user = User.objects.create(
            phone_number="+79998887766",
            first_name="John",
            last_name="Test",
            email="test@test1.com",
            is_active=True,
        )
        new_user.set_password("test_password1")
        new_user.save()
        
        new_cart = Cart.objects.create(user=new_user)
        
        with patch("cart.views.get_or_create_cart") as mock_get_or_create_cart:
            mock_get_or_create_cart.return_value = new_cart

            response = authorized_api_client.get(
                self.endpoint
            )
            assert response.status_code == 403
    
    def test_carts_synchronization(self, api_client, test_user):
        cart = Cart.objects.create(user=test_user)
        
        product = baker.make(
            Product,
            id=11,
            _quantity=1
        )

        CartItem.objects.create(cart=cart, product=product[0])
        
        response = api_client.get(
            self.endpoint
        )
        assert "cart_id" in response.cookies

        api_client.cookies["cart_id"] = response.cookies["cart_id"].value
        
        for _ in range(2):
            add_item_response = api_client.post(
                reverse("cart:cart_items"),
                data={"product_id": 11},
                format="json"
            )

        assert add_item_response.status_code == 201, f"{add_item_response.json()}"
        
        add_item_response_data = add_item_response.json()
        assert "product_id" in add_item_response_data
        assert add_item_response_data["product_id"] == 11
        
        credentials = {"username": test_user.username,
                       "password": "test_password"}
        
        auth_response = api_client.post(
            reverse("auth:obtain_jwt"),
            data=credentials,
            format="json"
        )

        assert not "cart_id" in auth_response.cookies
        
        auth_response_data = auth_response.json()
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {auth_response_data['access_token']}"
        )

        authorized_response = api_client.get(
            self.endpoint
        )

        assert authorized_response.status_code == 200
        assert cart.items.filter(product__pk=11).first().quantity == 3


@pytest.mark.django_db
class TestCartItemAPIView:
    @property
    def post_endpoint(self):
        return reverse("cart:cart_items")
    
    def get_patch_endpoint(self, pk):
        return reverse("cart:update_cart_item", kwargs={"pk": pk})
    
    @pytest.mark.parametrize("method, expected_serializer",
        [
            ("post", CartAddItemSerializer),
            ("patch", CartReduceItemQuantitySerializer)
        ]
    )
    def test_get_serializer_class(self, factory, method, expected_serializer):
        view = views.CartItemAPIView()
        request_method = getattr(factory, method)

        endpoint = self.post_endpoint if method == "post" else self.get_patch_endpoint(pk=1)
        request = request_method(endpoint, {} if method == "post" else None)

        view.request = request
        assert view.get_serializer_class() is expected_serializer

    @pytest.mark.parametrize("method",
        [
            "post", "patch"
        ]
    )
    def test_get_serializer_context(self, factory, method):
        view = views.CartItemAPIView.as_view()
        request_method = getattr(factory, method)

        endpoint = self.post_endpoint if method == "post" else self.get_patch_endpoint(pk=1)
        request = request_method(endpoint, {} if method == "post" else None)
        response = view(request, pk=1)
        
        view_instance = response.renderer_context["view"]
        context = view_instance.get_serializer_context()
        
        if method == "post":
            assert hasattr(context["request"], "cart")
            assert isinstance(context["request"].cart, Cart)
        else:
            assert not hasattr(context["request"], "cart")

    def test_partial_update(self, test_user_cart, authorized_api_client):
        cart_item_id_1 = CartItem.objects.select_related("product") \
                                 .order_by("product__pk").first()
        authorized_api_client.post(
            self.post_endpoint,
            data={"product_id": cart_item_id_1.product.pk},
            format="json"
        )

        endpoint = self.get_patch_endpoint(pk=cart_item_id_1.pk)
        response = authorized_api_client.patch(
            endpoint
        )
        assert response.status_code == 200

        endpoint = self.get_patch_endpoint(pk=cart_item_id_1.pk + 1)
        response = authorized_api_client.patch(
            endpoint
        )
        assert response.status_code == 200

        test_user_cart.refresh_from_db()
        assert test_user_cart.items.filter(pk=cart_item_id_1.pk).first().quantity == 1
        assert not test_user_cart.items.filter(pk=cart_item_id_1.pk + 1).exists()

