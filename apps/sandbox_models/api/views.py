from django.utils.translation import gettext_lazy as _
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.base.api.views import ApiGenericViewSet
from apps.core.constants import HttpMethods
from apps.sandbox_models.api.serializers import (
    ProductDocumentUploaderSerializer,
    ProductImageUploaderSerializer,
    ProductSerializer,
)
from apps.sandbox_models.models import Product


class ProductViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """User view set that represents common actions for basic user actions.
    Like: registration, verification, and password reset
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    messages = {"verification_successful": _("Email successful verified")}

    @action(
        methods=[HttpMethods.PUT.value],
        detail=True,
        serializer_class=ProductDocumentUploaderSerializer,
        parser_classes=(MultiPartParser,),
    )
    def upload_document(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(
        methods=[HttpMethods.PUT.value],
        detail=True,
        serializer_class=ProductImageUploaderSerializer,
        parser_classes=(MultiPartParser,),
    )
    def upload_image(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
