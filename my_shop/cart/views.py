from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from .models import Cart, CartItem
from . import serializers
from .services import get_or_create_cart, clear_cart, synchronize_carts
from .permission import IsCartOwner


class CartAPIView(generics.RetrieveDestroyAPIView):
    queryset = Cart.objects.prefetch_related("items").all()
    serializer_class = serializers.CartSerializer
    permission_classes = [IsCartOwner]

    def get_object(self):
        return get_or_create_cart(self.request)

    def destroy(self, request, *args, **kwargs):
        cart = self.get_object()
        if request.user.is_authenticated:
            clear_cart(cart)
        else:
            self.perform_destroy(cart)
        return Response({"detail": "Корзина очищена"},
                        status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        if request.user.is_authenticated and "cart_id" in request.COOKIES:
            synchronize_carts(request)
        return super().retrieve(request, *args, **kwargs)


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
        context["request"].cart = get_or_create_cart(self.request)
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

