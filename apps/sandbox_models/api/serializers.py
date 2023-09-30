from django.core.validators import FileExtensionValidator
from django.utils.timezone import now
from rest_framework import serializers

from apps.sandbox_models.models import Category, Product, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    product_name = serializers.CharField(source="name")
    days_created_ago = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name")
    product_tags = TagSerializer(many=True, read_only=True, source="tags")
    created_by = serializers.IntegerField(source="created_by_id")

    def get_days_created_ago(self, obj):
        return (now() - obj.created).days

    class Meta:
        depth = 0
        model = Product
        fields = "__all__"

    class FilterMeta:
        depth = 1
        filter_mapper = {
            "name": None,
            "created_by": {"type": "field", "filter_field": serializers.IntegerField(), "operations": ["equal"]},
            "options": {
                "type": "json_field_mapper",
                "fields": {"user": serializers.IntegerField(), "counter": serializers.IntegerField()},
                "many": True,
            },
        }
        filters = "__all__"


class ProductDocumentUploaderSerializer(serializers.ModelSerializer):
    document = serializers.FileField(
        required=True,
        allow_null=False,
        allow_empty_file=False,
        validators=[FileExtensionValidator(allowed_extensions=[".scv"])],
    )

    class Meta:
        model = Product
        fields = ("document",)


class ProductImageUploaderSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(
        required=True,
        allow_null=False,
        allow_empty_file=False,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"])],
    )

    class Meta:
        model = Product
        fields = ("image",)
