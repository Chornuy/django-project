# Generated by Django 4.2 on 2023-05-19 00:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_verified",
            field=models.BooleanField(default=False, verbose_name="email verification"),
        ),
    ]