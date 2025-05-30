from core.celery import app
from django.template.loader import render_to_string
from django.core.mail import send_mail

from .models import Order


@app.task
def send_order_email(order_id, user_email):
    order = Order.objects.get(id=order_id)
    
    subject = "Подтверждение заказа"
    html_message = render_to_string(
            "order_email.html",
            {"order": order}
        )
    
    send_mail(
        subject=subject,
        message="",
        from_email=None,
        recipient_list=[user_email],
        fail_silently=False,
        html_message=html_message
    )