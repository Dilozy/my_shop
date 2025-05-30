from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ["product"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "first_name", "last_name", "email",
                    "address", "city", "paid", "created",
                    "updated"]
    list_filter = ["paid", "created", "updated"]
    inlines = [OrderItemInline]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if request.user.is_authenticated:
            initial.update({
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
            })
        return initial

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj and obj.user:
            readonly_fields.extend(["first_name", "last_name", "email"])
        return readonly_fields
