"""
URL configuration for my_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import PasswordChangeView
from django.http import JsonResponse


def custom_404(request, exception=None):
    return JsonResponse({'error': ['Not found.']}, status=404)

handler404 = 'core.urls.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/user/<int:user_id>/password/', 
         PasswordChangeView.as_view(), 
         name='admin_password_change'),
    path('api/v1/users/', include('user_account.urls', namespace='users')),
    path('api/v1/auth/', include('authentication.urls', namespace='auth')),
    path('api/v1/', include('goods.urls', namespace='goods')),
    path('api/v1/', include('cart.urls', namespace='cart'))
]
