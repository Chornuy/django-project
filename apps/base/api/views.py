from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.base.response import ActionResponse, transform_status_code_to_message


class ApiGenericViewSet(GenericViewSet):
    """Modified view for unification of response messages"""

    messages = {}

    def get_message(self, message_code: str) -> str:
        """Method return translated message for detail description of response data

        Args:
            message_code (str): key of Class attribute of view

        Returns:
            str: Translated message
        """
        return self.messages[message_code]

    def create_successful_response(
        self,
        message_code: str = None,
        status_code: int = status.HTTP_200_OK,
        action_response_status: str = None,
        data: Any = None,
    ) -> Response:
        """Method helper to convert Django response in standard unified way of Api response

        Args:
            message_code (str): Key for message in response
            status_code (int): Status code for response
            action_response_status (str|None): Optional response status constant of response object
            data (Any): data for response

        Returns:
            Response: Django Response object
        """
        action_response_status = (
            action_response_status if action_response_status else transform_status_code_to_message(status_code)
        )

        message = self.get_message(message_code) if message_code else None
        return Response(
            data=ActionResponse(status=action_response_status, message=message, data=data), status=status_code
        )


class DynamicFieldApiViewMixin:
    def __init__(self, **kwargs):
        super(DynamicFieldApiViewMixin).__init__(**kwargs)
        self.selected_fields = None

    def get_serializer_context(self):
        return {
            "request": self.request,
            "format": self.format_kwarg,
            "view": self,
            "selected_fields": self.selected_fields,
        }
