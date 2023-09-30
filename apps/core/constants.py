from enum import Enum


class HttpMethods(str, Enum):
    """Small enum class to unify Https methods.
    For some reason Django and DRF do not have constants for such purpose

    See: https://github.com/encode/django-rest-framework/issues/2721

    Example:
        class ExampleView(GenericViewSet):

            @action(methods=[HttpMethods.GET], detail=False)
            def ping(self, request):
                return Response(data="pong")
    """

    POST: str = "POST"
    GET: str = "GET"
    PUT: str = "PUT"
    PATCH: str = "PATCH"
    DELETE: str = "DELETE"
