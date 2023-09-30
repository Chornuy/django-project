from django.conf import settings

from apps.api_authentication.api.api_router import router as auth_router
from apps.sandbox_models.api.api_router import router as product_router
from apps.users.api.api_router import router as user_router
from apps.utils.router import DefaultApiRouter, SimpleApiRouter

if settings.DEBUG:
    router = DefaultApiRouter()
else:
    router = SimpleApiRouter()

# router.register("users", UserViewSet)
router.extend(user_router)
router.extend(auth_router)
router.extend(product_router)
#
# router.register('echo', EchoViewSet)
app_name = "api"
urlpatterns = router.urls
