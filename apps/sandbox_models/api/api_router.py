from django.conf import settings

from apps.sandbox_models.api.views import ProductViewSet
from apps.utils.router import DefaultApiRouter, SimpleApiRouter

if settings.DEBUG:
    router = DefaultApiRouter()
else:
    router = SimpleApiRouter()

URL_VERSION = r"^(?P<version>v[1])"

router.register(f"v1/products", ProductViewSet, basename="product")
