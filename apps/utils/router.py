from rest_framework import routers


class RouterMixin:
    def extend(self, router):
        self.registry.extend(router.registry)


class DefaultApiRouter(RouterMixin, routers.DefaultRouter):
    pass


class SimpleApiRouter(RouterMixin, routers.SimpleRouter):
    pass
