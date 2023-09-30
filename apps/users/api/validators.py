from typing import Any

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError


class FieldMatchValidator:
    """Base validator for to check if two fields should match or mismatch.

    Examples:
        class PasswordMatchMixin(metaclass=serializers.SerializerMetaclass):
            password = PasswordField(
                write_only=True,
                required=True,
                max_length=256,
            )
            password2 = serializers.CharField(
                write_only=True,
                required=True,
                max_length=256,
            )

            class Meta:
                model = User
                fields = ["password", "password2"]
                validators = [FieldMatchValidator("password", "password2", error_code="password_mismatch")]

    """

    match_message = _("Fields: {field_one} and {field_two} does not match")
    mismatch_message = _("Fields: {field_one} and {field_two} are same")
    requires_context = False

    def __init__(self, field_one: str, field_two: str, error_code: str = None, should_match=True) -> None:
        """Init method

        Args:
            field_one (str): name of field in serializer class
            field_two (str): name of second field to check
            should_match (bool): tell to check if two fields are matched or mismatched.
             If should_match == True - Will raise error if two fields are same
             If should_match == False - Will raise error if two fields mismatch
        Raises:
            ValueError: in case should_match and should_mismatch are supplied
        """
        self.error_code = error_code
        self.should_match = should_match
        self.field_one = field_one
        self.field_two = field_two

    def _check_mismatch(self, field_one_value: Any, field_two_value: Any) -> None:
        """Run check that both field are not the same

        Args:
            field_one_value: value of first field
            field_two_value: value of second field

        Raises:
            ValidationError: if two fields match

        Returns:
            None
        """
        if field_one_value == field_two_value:
            message = self.mismatch_message.format(field_one=self.field_one, field_two=self.field_two)
            raise ValidationError(message, code=self.error_code)

    def _check_match(self, field_one_value: Any, field_two_value: Any) -> None:
        """Run check that both field are the same

        Args:
            field_one_value: value of first field
            field_two_value: value of second field

        Raises:
            ValidationError: if two fields mismatch

        Returns:
            None

        """
        if not field_one_value == field_two_value:
            message = self.match_message.format(field_one=self.field_one, field_two=self.field_two)
            raise ValidationError(message, code=self.error_code)

    def __call__(self, attrs: dict) -> None:
        """Validation call. Take two fields values check if they match or mismatch.

        Args:
            attrs (dict): Serializer data with fields value inside

        Raises:
            ValidationError: If fields match or mismatch

        Returns:
            None

        """
        field_one_value = attrs[self.field_one]
        field_two_value = attrs[self.field_two]
        if self.should_match:
            self._check_match(field_one_value, field_two_value)
        else:
            self._check_mismatch(field_one_value, field_two_value)
