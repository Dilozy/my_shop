from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from .models import Cart, CartItem
from . import serializers
from .services import get_or_create_cart, clear_cart
from .permission import IsCartOwner


class CartAPIView(generics.RetrieveDestroyAPIView):
    queryset = Cart.objects.prefetch_related("items").all()
    serializer_class = serializers.CartSerializer
    permission_classes = [IsCartOwner]

    def get_object(self):
        cart = get_or_create_cart(self.request.user, self.request.COOKIES)
        self.check_object_permissions(self.request, cart)
        return cart

    def destroy(self, request, *args, **kwargs):
        cart = self.get_object()
        clear_cart(cart,
                    is_authenticated=request.user.is_authenticated)

        return Response({"detail": "Корзина очищена"},
                        status=status.HTTP_200_OK)


class CartItemAPIView(generics.UpdateAPIView,
                      generics.CreateAPIView):
    queryset = CartItem.objects.select_related("cart").all()
    permission_classes = [IsCartOwner]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.CartAddItemSerializer
        return serializers.CartReduceItemQuantitySerializer
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        
        if self.request.method == "POST":
            context["request"].cart = get_or_create_cart(self.request.user,
                                                        self.request.COOKIES)
        
        return context
    
    def partial_update(self, request, *args, **kwargs):
        target_item = self.get_object()
        serializer = self.get_serializer(target_item,
                                         data=request.data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)

        updated_item = serializer.save()
        if updated_item.quantity == 0:
            updated_item.delete()
        return Response(serializer.data)

