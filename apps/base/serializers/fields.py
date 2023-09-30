from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated

User = get_user_model()


class BasePasswordField(serializers.CharField):
    """Class helper for work with password field in Serializer classes.
    Set styling for field, and provide method for taking a user from current request.

    """

    def __init__(self, *args, **kwargs):
        kwargs["write_only"] = True
        kwargs["style"] = {"input_type": "password"}
        self.user = kwargs.pop("user", None)
        self.user_from_request = kwargs.pop("validate_password_for_user", True)
        super().__init__(*args, **kwargs)

    def get_user(self) -> User | None:
        """Method take user from current request and set to self.user attribute.
        If user not logged in system will set and return None

        Returns:
            Optional[User]: None if user not logged in system or current user in system

        """
        if not self.user and self.user_from_request:
            if self.context:
                request = self.context.get("request")
                if request.user.is_authenticated:
                    self.user = request.user
        return self.user


class PasswordField(BasePasswordField):
    """Serializer Field class, helps to check if that was set by user is strong enough.
    For unification class uses password validation that set in Django settings: settings.AUTH_PASSWORD_VALIDATORS

    Examples:
        class PasswordMatch(serializers.Serializer):
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
    """

    def __init__(self, *args, **kwargs):
        self.validate_password = kwargs.pop("validate_password", True)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data: str) -> str:
        """Method validate entered password in case when new password set.
        Run default validators for password field from settings.AUTH_PASSWORD_VALIDATORS

        Args:
            data (str): new password that was entered from user

        Returns:
            str: Valid password for create a new password

        Raises:
            ValidationError: in case if password to weak, or not meet requirements in settings.AUTH_PASSWORD_VALIDATORS
        """
        if self.validate_password:
            password_validation.validate_password(data, user=self.get_user())
        return super().to_internal_value(data)


class CurrentUserPasswordField(BasePasswordField):
    """Serializer Field class, that helps to validate if user entered his current password.
    Uses in the cases when data that user want to change need a password check.

    Examples:
        class PasswordMatch(serializers.Serializer):
            current_password = CurrentUserPasswordField(required=True)

            new_password = PasswordField(
                write_only=True,
                required=True,
                max_length=256,
            )
            new_password2 = serializers.CharField(
                write_only=True,
                required=True,
                max_length=256,
            )
    """

    default_error_messages = {
        **BasePasswordField.default_error_messages,
        **{"password_not_match": _("Ensure this field has at least {min_length} characters.")},
    }

    def to_internal_value(self, data: str) -> str:
        """Method check if current password are the same that user set.
        Need in case when user request changes of sensitive data (Example: change current password)
        to prove user identity

        Args:
            data (str): current password for user

        Returns:
            str: Password for current user

        Raises:
            ValidationError: in case if password not match for user
        """
        user = self.get_user()

        # Most cases this behaviour should be resolved in ApiView class with permissions.
        # This protection is more for developers need
        if not user:
            raise NotAuthenticated()

        # Check if current password match, in not raise password not match
        if not user.check_password(data):
            self.fail("password_not_match")

        return super().to_internal_value(data)
