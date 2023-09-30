from django.conf import settings

from apps.api_authentication.api.views import AuthApiView
from apps.utils.router import DefaultApiRouter, SimpleApiRouter

if settings.DEBUG:
    router = DefaultApiRouter()
else:
    router = SimpleApiRouter()

URL_VERSION = r"^(?P<version>v[1])"

router.register("v1/auth", AuthApiView, basename="auth")
