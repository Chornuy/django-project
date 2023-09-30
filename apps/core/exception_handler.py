from dataclasses import asdict

from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.settings import package_settings
from drf_standardized_errors.types import ErrorType
from rest_framework import exceptions

from apps.base.response import ErrorField, ErrorResponse


class ApiResponseExceptionFormatter(ExceptionFormatter):
    def get_error_response(self, error_type: ErrorType, errors: list[ErrorField]) -> ErrorResponse:
        """

        Args:
            error_type:
            errors:

        Returns:

        """
        return ErrorResponse(status=error_type, errors=errors, message=self.exc.default_detail)

    def get_errors(self) -> list[ErrorField]:
        """
        Account for validation errors in nested serializers by returning a list
        of errors instead of a nested dict
        """
        return flatten_errors(self.exc.detail)

    def format_error_response(self, error_response: ErrorResponse):
        return asdict(error_response)


def flatten_errors(detail: list | dict | exceptions.ErrorDetail, attr=None, index=None) -> list[ErrorField]:
    """The code and flow was taken from https://github.com/ghazi-git/drf-standardized-errors
    but for the project needed only flatten_errors function. Just to reduce dependencies and size of project

    Examples:
        convert this:
        {
            "password": [
                ErrorDetail("This password is too short.", code="password_too_short"),
                ErrorDetail("The password is too similar to the username.", code="password_too_similar"),
            ],
            "linked_accounts" [
                {},
                {"email": [ErrorDetail("Enter a valid email address.", code="invalid")]},
            ]
        }
        to:
        {
            "type": "validation_error",
            "errors": [
                {
                    "code": "password_too_short",
                    "detail": "This password is too short.",
                    "attr": "password"
                },
                {
                    "code": "password_too_similar",
                    "detail": "The password is too similar to the username.",
                    "attr": "password"
                },
                {
                    "code": "invalid",
                    "detail": "Enter a valid email address.",
                    "attr": "linked_accounts.1.email"
                }
            ]
        }
    """

    if not detail:
        return []

    elif isinstance(detail, list):
        first_item, *rest = detail
        if not isinstance(first_item, exceptions.ErrorDetail):
            index = 0 if index is None else index + 1
            if attr:
                new_attr = f"{attr}{package_settings.NESTED_FIELD_SEPARATOR}{index}"
            else:
                new_attr = str(index)
            return flatten_errors(first_item, new_attr, index) + flatten_errors(rest, attr, index)
        else:
            return flatten_errors(first_item, attr, index) + flatten_errors(rest, attr, index)
    elif isinstance(detail, dict):
        (key, value), *rest = list(detail.items())
        if attr:
            key = f"{attr}{package_settings.NESTED_FIELD_SEPARATOR}{key}"
        return flatten_errors(value, key) + flatten_errors(dict(rest), attr)
    else:
        return [ErrorField(code=detail.code, message=str(detail), field=attr)]
