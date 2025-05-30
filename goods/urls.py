from rest_framework.routers import DefaultRouter

from goods import views


app_name = "goods"


router = DefaultRouter()
router.register("products", views.ProductViewSet, basename="products")
router.register("categories", views.CategoryViewSet, basename="categories")
urlpatterns = router.urls