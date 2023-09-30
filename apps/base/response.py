from dataclasses import dataclass
from enum import Enum
from typing import Any

from rest_framework.status import is_client_error, is_redirect, is_server_error, is_success


class ActionResponseStatuses(str, Enum):
    """Statuses for ActionResponse object, for reserve more custom statuses in response"""

    SUCCESS: str = "success"
    FAIL: str = "fail"
    CLIENT_ERROR: str = "client_error"
    SERVER_ERROR: str = "internal_server_error"
    ACTION_REQUIRED: str = "action_required"


@dataclass
class ActionResponse:
    """Custom class for more detail and unify way to response from apis"""

    message: str
    status: str
    data: Any = None

    def __iter__(self):
        """Method to support transformation from object to dict by calling dict()
        Examples:
            response_obj = ActionResponse()
            dict(response_obj)
        """
        return iter([(k, v) for k, v in self.__dict__.items()])


@dataclass
class ErrorResponse:
    """Error response type"""

    message: str
    status: str
    errors: list


@dataclass
class ErrorField:
    code: str
    message: str
    field: str


def transform_status_code_to_message(status_code: int):
    """Transform int response status code to str representation for ActionResponse object

    Args:
        status_code (int): HTTP status code represent status code of response

    Returns:
        str: ActionResponseStatuses str
    """

    if is_success(status_code):
        return ActionResponseStatuses.SUCCESS

    if is_redirect(status_code):
        return ActionResponseStatuses.ACTION_REQUIRED

    if is_client_error(status_code):
        return ActionResponseStatuses.CLIENT_ERROR

    if is_server_error(status_code):
        return ActionResponseStatuses.SERVER_ERROR
