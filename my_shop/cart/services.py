from .models import Cart, CartItem


def get_or_create_cart(user, cookies):
    if user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=user,
                                             defaults={"user": user})
        
    else:
        cart_id = cookies.get("cart_id")
        if not cart_id:
            cart = Cart.objects.create()
        else:
            cart, _ = Cart.objects.get_or_create(cart_id=cart_id, user__isnull=True,
                                                 defaults={})
    
    return cart


def add_item_to_cart(cart, target_product):
    cart_item, created = CartItem.objects.get_or_create(cart=cart,
                                                        product=target_product,
                                                        defaults={"cart": cart,
                                                                  "product": target_product}
                                                        )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return cart_item


def synchronize_carts(user, cookies):
    guest_cart = Cart.objects.get(pk=cookies.get("cart_id"))
    user_cart = get_or_create_cart(user, cookies)

    user_items = {item.product.pk: item for item in 
                 CartItem.objects.select_related("product").filter(cart=user_cart)}
    guest_items = CartItem.objects.select_related("product").filter(cart=guest_cart)

    update_quantity_items = []
    update_cart_items = []

    for guest_item in guest_items:
        if (guest_item_product_id := guest_item.product.pk) in user_items:
            user_item = user_items[guest_item_product_id]
            user_item.quantity += guest_item.quantity
            update_quantity_items.append(user_item)
        else:
            guest_item.cart = user_cart
            update_cart_items.append(guest_item)
    
    if update_cart_items:
        CartItem.objects.bulk_update(update_cart_items, ["cart"])
    if update_quantity_items:
        CartItem.objects.bulk_update(update_quantity_items, ["quantity"])
    
    guest_cart.delete()


def clear_cart(cart):
    CartItem.objects.filter(cart=cart).delete()
