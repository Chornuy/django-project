from django.conf import settings

from apps.api_authentication.api.api_router import router as auth_router
from apps.users.api.api_router import router as user_router
from apps.utils.router import DefaultApiRouter, SimpleApiRouter

if settings.DEBUG:
    router = DefaultApiRouter()
else:
    router = SimpleApiRouter()

# Auth router
router.extend(auth_router)

# User apis
router.extend(user_router)

app_name = "api"
urlpatterns = router.urls
