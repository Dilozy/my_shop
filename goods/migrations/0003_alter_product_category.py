# Generated by Django 5.1.7 on 2025-05-29 08:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0002_alter_product_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='goods.category', verbose_name='Категория'),
        ),
    ]
