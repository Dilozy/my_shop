from rest_framework import permissions


class IsCartOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        cart = obj.cart
        if request.user.is_authenticated:
            return cart.user == request.user
        else:
            return request.COOKIES.get("cart_id") == str(cart.cart_id)
