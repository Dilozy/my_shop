# Generated by Django 5.1.7 on 2025-04-23 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_account', '0004_alter_user_is_active_alter_user_is_admin_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=255, verbose_name='E-mail'),
        ),
        migrations.AlterField(
            model_name='user',
            name='password',
            field=models.CharField(max_length=128, verbose_name='password'),
        ),
    ]
