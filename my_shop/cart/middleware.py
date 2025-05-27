from .services import get_or_create_cart


class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated and "cart_id" in request.COOKIES:
            response.delete_cookie("cart_id")
        
        # Если пользователь аноним и нет корзины — создаём и ставим cookie
        if not request.user.is_authenticated and not request.COOKIES.get("cart_id"):
            cart = get_or_create_cart(request.user, request.COOKIES)
            response.set_cookie(
                key="cart_id",
                value=str(cart.cart_id),
                httponly=True,
                samesite="Lax",
                max_age=86400
            )

        return response
    