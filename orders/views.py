from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from cart.permission import IsCartOwner
from .models import Order, OrderItem
from . import serializers
from .services import get_cart
from cart.models import Cart, CartItem
from cart.services import clear_cart


class ListCreateOrderAPIView(generics.ListCreateAPIView):
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated(), IsCartOwner()]
        return [IsCartOwner()]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.ListRetrieveOrderSerializer
        return serializers.CreateOrderSerializer

    def create(self, request, *args, **kwargs):
        try:
            user_cart = get_cart(request)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Корзина не найдена"},
                status=status.HTTP_404_NOT_FOUND
                )
        except ValidationError:
            return Response(
                {"error": "Отсутствует идентификатор корзины в cookies"},
                status=status.HTTP_400_BAD_REQUEST
                )
        
        cart_items = CartItem.objects.filter(cart=user_cart)
        context = {"cart_items": cart_items,
                   "request": request}
        serializer = serializers.CreateOrderSerializer(data=request.data,
                                                       context=context)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        clear_cart(user_cart,
                    is_authenticated=request.user.is_authenticated)

        return Response({"detail": "Заказ успешно оформлен. "
                        "Детали заказа высланы на вашу электронную почту"},
                        status=status.HTTP_201_CREATED)
        

class RetrieveOrderAPIView(generics.RetrieveAPIView):
    serializer_class = serializers.ListRetrieveOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


        
