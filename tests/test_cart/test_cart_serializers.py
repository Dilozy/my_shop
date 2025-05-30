import pytest
from model_bakery import baker
from rest_framework.exceptions import ValidationError

from goods.models import Product
from cart.models import CartItem, Cart
from cart import serializers


@pytest.mark.django_db
class TestCartReduceItemQuantitySerializer:
    @pytest.fixture
    def test_item(self, test_user):
        product = baker.make(
            Product,
            _quantity=1
        )
        cart = Cart.objects.create(user=test_user)

        return CartItem.objects.create(product=product[0], cart=cart, quantity=10)
    
    def test_serializer_update_method(self, test_item):
        serializer = serializers.CartReduceItemQuantitySerializer(test_item,
                                                                  data={},
                                                                  partial=True
                                                                  )
        serializer.is_valid(raise_exception=True)
        
        updated_item = serializer.save()
        assert updated_item.quantity == 9

    def test_serializer_update_method_with_invalid_quantity(self, test_item):
        test_item.quantity = 0
        test_item.save()
        
        serializer = serializers.CartReduceItemQuantitySerializer(test_item,
                                                                  data={},
                                                                  partial=True
                                                                  )
        
        
        with pytest.raises(ValidationError, match="Товар уже отсутствует в корзине"):
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestCartSerializer:
    def test_to_representation_method(self, test_user):
        cart = Cart.objects.create(user=test_user)
        serializer = serializers.CartSerializer(cart)
        assert serializer.data == {"detail": "Ваша корзина пуста"}
        
        test_products = baker.make(
            Product,
            _quantity=1
        )

        test_item = CartItem.objects.create(product=test_products[0],
                                            cart=cart)
        serializer = serializers.CartSerializer(cart)
        assert test_item.id == serializer.data["items"][0]["id"]


@pytest.mark.django_db
class TestCartAddItemSerializer:
    def test_serializer_with_valid_data(self, test_user_cart):
        add_item = test_user_cart.items.first()
        data = {"product_id": add_item.product.id}
        serializer = serializers.CartAddItemSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        assert serializer.data == data

    def test_serializer_with_invalid_data(self):
        data = {"product_id": -1}
        serializer = serializers.CartAddItemSerializer(data=data)
        with pytest.raises(ValidationError, match="Продукт не найден"):
            serializer.is_valid(raise_exception=True)
