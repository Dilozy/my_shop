from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import send_mail


@shared_task
def send_order_email(order, user):
    subject = "Подтверждение заказа"
    html_message = render_to_string(
            "activation_email.html",
            {"user": user, "order": order}
        )
    
    send_mail(
        subject=subject,
        message="",
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
        html_message=html_message
    )