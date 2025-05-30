from rest_framework import serializers

from .models import Cart, CartItem
from goods.serializers import ProductSerializer
from goods.models import Product
from .services import add_item_to_cart


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity"]


class CartAddItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()

    def validate(self, data):
        try:
            product = Product.objects.get(pk=data["product_id"])
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id": "Продукт не найден"})
        
        data["product"] = product
        return data

    def create(self, validated_data):
        cart = self.context["request"].cart
        cart_item = add_item_to_cart(cart,
                                     validated_data["product"])
        return cart_item

class CartSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2,
                                           read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cart
        fields = ["items", "total_price"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if len(data["items"]) == 0:
            data = {"detail": "Ваша корзина пуста"}
        return data


class CartReduceItemQuantitySerializer(serializers.ModelSerializer):
    cart = CartSerializer(read_only=True)
    
    class Meta:
        model = CartItem
        fields = ["cart"]

    def validate(self, data):
        if self.instance.quantity <= 0:
            raise serializers.ValidationError({"error": "Товар уже отсутствует в корзине"})
        return data

    def update(self, instance, validated_data):
        instance.quantity -= 1
        
        # Не даём уйти в отрицательные значения (запасная проверка)
        if instance.quantity < 0:
            instance.quantity = 0
            
        instance.save()
        return instance