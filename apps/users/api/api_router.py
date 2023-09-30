from django.conf import settings

from apps.users.api.views import UserViewSet
from apps.utils.router import DefaultApiRouter, SimpleApiRouter

if settings.DEBUG:
    router = DefaultApiRouter()
else:
    router = SimpleApiRouter()

URL_VERSION = r"^(?P<version>v[1])"

router.register(f"v1/users", UserViewSet)
