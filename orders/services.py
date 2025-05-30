from rest_framework.exceptions import ValidationError

from cart.models import Cart


def get_cart(request):
    user = request.user
    
    if user.is_authenticated:
        return Cart.objects.get(user=user)

    else:
        cart_id = request.COOKIES.get("cart_id")
        if cart_id is not None:
            return Cart.objects.get(pk=cart_id)
        else:
            raise ValidationError()
        
