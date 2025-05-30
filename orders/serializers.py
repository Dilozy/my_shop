from rest_framework import serializers

from .models import Order, OrderItem
from goods.serializers import ProductSerializer
from .services import send_order_email


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "cost"]


class ListRetrieveOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(read_only=True, many=True)
    
    class Meta:
        model = Order
        fields = ["id", "order_uuid", "first_name",
                  "last_name", "email", "address",
                  "city", "created", "updated",
                  "paid", "status", "total_cost",
                  "items",]


class CreateOrderSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        user = self.context.get("request").user
        if user.is_authenticated:
            prepopulated_fields = ("first_name", "last_name", "email")
            for field in prepopulated_fields:
                self.fields[field].required = False
                self.fields[field].initial = getattr(user, field)
    
    def validate(self, data):
        if (user := self.context["request"].user).is_authenticated:
            data["first_name"] = data.get("first_name", user.first_name)
            data["last_name"] = data.get("last_name", user.last_name)
            data["email"] = data.get("email", user.email)

        if len(self.context["cart_items"]) == 0:
            raise serializers.ValidationError(
                {"error": "Ваша корзина пуста, вы не можете оформить заказ"}
                )
        return data
    
    def create(self, validated_data):
        user = self.context["request"].user
    
        new_order = Order.objects.create(
            user=user if user.is_authenticated else None,
            **validated_data
            )
    
        order_items = [OrderItem(order=new_order,
                                 product=item.product,
                                 price=item.product.price,
                                 quantity=item.quantity)
                       for item in self.context["cart_items"]]
        OrderItem.objects.bulk_create(order_items)

        return new_order
    
    def save(self):
        self.instance = self.create(self.validated_data)
        send_order_email.delay(self.instance,
                               self.context["request"].user)
        return self.instance

    class Meta:
        model = Order
        fields = ["first_name", "last_name", "email",
                  "address", "city"]