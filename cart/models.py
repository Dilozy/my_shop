import uuid

from django.contrib.auth import get_user_model
from django.db import models

from goods.models import Product


User = get_user_model()


class Cart(models.Model):
    cart_id = models.UUIDField(primary_key=True, default=uuid.uuid4(),
                               unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

