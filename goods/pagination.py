from rest_framework.pagination import LimitOffsetPagination


class ProductsPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 30