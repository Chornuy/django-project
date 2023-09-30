from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.views import TokenViewBase

from apps.base.api.views import ApiGenericViewSet
from apps.core.constants import HttpMethods


class TokenActionViewBase(ApiGenericViewSet, TokenViewBase):
    """"""

    def process_token_base_action(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class AuthApiView(TokenActionViewBase):
    @action(methods=[HttpMethods.POST.value], detail=False, _serializer_class=api_settings.TOKEN_OBTAIN_SERIALIZER)
    def token(self, request, *args, **kwargs):
        return self.process_token_base_action(request, *args, **kwargs)

    @action(methods=[HttpMethods.POST.value], detail=False, _serializer_class=api_settings.TOKEN_REFRESH_SERIALIZER)
    def refresh(self, request, *args, **kwargs):
        return self.process_token_base_action(request, *args, **kwargs)

    @action(methods=[HttpMethods.POST.value], detail=False, _serializer_class=api_settings.TOKEN_VERIFY_SERIALIZER)
    def verify(self, request, *args, **kwargs):
        return self.process_token_base_action(request, *args, **kwargs)

    @action(methods=[HttpMethods.GET.value], detail=False)
    def logout(self, request, *args, **kwargs):
        return Response(data="OLO")
