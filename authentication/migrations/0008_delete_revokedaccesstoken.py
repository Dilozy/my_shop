# Generated by Django 5.1.7 on 2025-05-01 13:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_revokedaccesstoken'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RevokedAccessToken',
        ),
    ]
