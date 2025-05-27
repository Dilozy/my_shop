from rest_framework import permissions


class IsCartOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            if hasattr(obj, "user"):
                return obj.user == request.user
            elif hasattr(obj, "cart"):
                return obj.cart.user == request.user
            return False
        else:
            if not request.COOKIES.get("cart_id"):
                return True  # ← Разрешаем анонимный доступ
            return request.COOKIES.get("cart_id") == str(obj.cart_id)
