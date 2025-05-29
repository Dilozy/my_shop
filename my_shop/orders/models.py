import uuid

from django.db import models
from django.conf import settings

from goods.models import Product


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = "pending", "Ожидает оплаты"
        PAID = "paid", "Оплачен"
        PACKING = "packing", "В сборке"
        DELIVERING = "delivering", "Доставляется"
        COMPLETED = "completed", "Выполнен"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    address = models.TextField(verbose_name="Адрес")
    city = models.CharField(max_length=100,
                            verbose_name="Город")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False, verbose_name="Оплачен")
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        verbose_name="Статус заказа"
    )

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["-created"])
        ]

    def __str__(self):
        return f"Order: {self.id}"
    
    @property
    def total_cost(self):
        return sum(item.cost for item in self.items.all())
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order,
                              on_delete=models.CASCADE,
                              related_name="items")
    product = models.ForeignKey(Product,
                                on_delete=models.CASCADE,
                                related_name="order_products")
    price = models.DecimalField(max_digits=10,
                                decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)
    
    @property
    def cost(self):
        return self.price * self.quantity