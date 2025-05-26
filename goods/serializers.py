from rest_framework import serializers

from .models import Product, Category


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
        )
    category_name = serializers.StringRelatedField(source="category",
                                                   read_only=True)
    
    class Meta:
        model = Product
        fields = ["name", "category", "description",
                  "price", "available", "category_name"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name"]