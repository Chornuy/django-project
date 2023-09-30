import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
User = get_user_model()


class Category(models.Model):
    name = models.TextField(blank=False, null=False, max_length=255, unique=True)


class Tag(models.Model):
    name = models.TextField(blank=False, null=False, max_length=255, unique=True)


PRODUCT_FOLDER = "products/"


def get_upload_to(instance, filename):
    return f"{PRODUCT_FOLDER}/{instance.pk}/{filename}"

    # IntegerFieldOperation,
    # FloatFieldOperation,
    # BooleanFieldOperation,
    # CharFieldFieldOperation,
    # DateFieldOperation,
    # DateTimeFieldOperation,
    # DurationFieldOperation,
    # EmailFieldFieldOperation,
    # FileFieldOperation,
    # ImageFieldOperation,
    # SlugFieldOperation,
    # URLFieldOperation,
    # UUIDFieldOperation,
    # IPAddressFieldOperation,
    # FilePathFieldOperation,


class Product(models.Model):
    name = models.TextField(null=False, blank=False, max_length=255, unique=True)
    rating = models.PositiveBigIntegerField(
        null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    float_index = models.FloatField(
        null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    price = models.DecimalField(max_digits=100, decimal_places=10, default=10)
    created = models.DateTimeField(blank=False, null=False, auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.RESTRICT, null=False)
    tags = models.ManyToManyField(Tag)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    options = models.JSONField(null=True, blank=False)

    url_field = models.URLField(null=True, blank=False, max_length=200, default="http://localhost/")
    uuid_field = models.UUIDField(null=True, blank=False, default=uuid.uuid4, editable=False)
    new_product = models.DurationField(null=True, blank=False, default=timedelta(days=1))

    is_active = models.BooleanField(null=True, blank=False, default=False)

    image = models.ImageField(
        null=True,
        blank=False,
        upload_to=get_upload_to,
        validators=[FileExtensionValidator(allowed_extensions=[".jpg", ".jpeg", ".png"])],
    )

    document = models.FileField(
        null=True,
        blank=False,
        upload_to=get_upload_to,
        validators=[FileExtensionValidator(allowed_extensions=[".scv"])],
    )

    ip_address = models.GenericIPAddressField(null=True, blank=False, default="127.0.0.1")

    class ProductStatus(models.TextChoices):
        CREATED = "CREATED", _("Created")
        DEACTIVATED = "DEACTIVATED", _("Deactivated")
        ACTIVE = "ACTIVE", _("Active")

    status = models.CharField(
        max_length=255,
        choices=ProductStatus.choices,
        default=ProductStatus.CREATED,
    )

    @property
    def full_name(self):
        return f"{self.name}_{self.category.name}"
