# Generated by Django 4.2 on 2023-07-04 12:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sandbox_models", "0005_product_float_index_product_ip_address_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="file_path",
            field=models.FilePathField(default="Downloads", null=True),
        ),
    ]