from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()

NOT_VERIFIED_MESSAGE = _("Please verify email first")
NOT_VERIFIED_CODE = "not_verified_email_user"


def user_rule_auth_active_and_verified(user: User) -> bool:
    """Function rule for authentication.
    By default, we authenticate users that active and verified their email

    Args:
        user (User): User model object

    Raises:
        AuthenticationFailed: if user not verify his email

    Returns:
        bool: if user can auth in system

    """

    if user is None:
        return False

    if not user.is_active:
        return False

    # Small Hack for raising Auth error for custom message for user that not verified.
    # Look for: class TokenObtainSerializer(serializers.Serializer) in rest_framework_simplejwt.serializers.py
    #
    # api_settings.USER_AUTHENTICATION_RULE(self.user):
    # expect to return bool. By default, it will generate error message "not_active_account"
    # For generation message for user that he still not verify email, this function for not verified user
    # raise AuthenticationFailed with message for not verified users

    if not user.is_verified:
        raise AuthenticationFailed(
            NOT_VERIFIED_MESSAGE,
            NOT_VERIFIED_CODE,
        )

    return True
