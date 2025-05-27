import uuid

from django.conf import settings
from django.db import models

from goods.models import Product


class Cart(models.Model):
    cart_id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                               unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                null=True, blank=True,
                                related_name="cart")
    created = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        return sum(
            item.product.price * item.quantity
            for item in self.items.select_related("product").all()
        )

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

