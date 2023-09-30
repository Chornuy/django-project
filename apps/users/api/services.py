from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.request import Request

from apps.utils.email import send_from_template_email

User = get_user_model()

token_generator = default_token_generator

EMAIL_VERIFICATION_ACTION = "api:user-verify"
EMAIL_VERIFICATION_TEMPLATE = "registration/email_verification.html"
EMAIL_VERIFICATION_SUBJECT = "registration/email_verification_subject.txt"

EMAIL_RESET_PASSWORD_ACTION = "api:user-set-new-password"
EMAIL_RESET_PASSWORD_TEMPLATE = "registration/email_reset_password.html"
EMAIL_RESET_PASSWORD_SUBJECT = "registration/email_reset_password_subject.txt"


def generate_uid_and_token_from_user(user: User) -> dict:
    """Generate temporary

    Args:
        user:

    Returns:

    """
    return {
        "uid64": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": token_generator.make_token(user),
    }


def send_verify_email(
    email_template_html: str, email_template_subject: str, view_action: str, user: User, request: Request
) -> None:
    """

    Args:
        email_template_html:
        email_template_subject:
        view_action:
        user:
        request:

    Returns:

    """

    action_params = generate_uid_and_token_from_user(user)
    verification_link = reverse(view_action, kwargs=action_params)
    full_url_verification_url = request.build_absolute_uri(verification_link)
    user_email = getattr(user, User.get_email_field_name())

    template_email_context = {"verification_absolute_url": full_url_verification_url, "domain": settings.PROJECT_NAME}

    send_from_template_email(
        subject_template_name=email_template_subject,
        email_template_name=email_template_html,
        context=template_email_context,
        from_email=settings.WEBSITE_EMAIL,
        to_email=user_email,
    )


def send_verification_email_after_registration(user: User, request: Request) -> None:
    """

    Args:
        user:
        request:

    Returns:

    """
    return send_verify_email(
        view_action=EMAIL_VERIFICATION_ACTION,
        email_template_html=EMAIL_VERIFICATION_TEMPLATE,
        email_template_subject=EMAIL_VERIFICATION_SUBJECT,
        user=user,
        request=request,
    )


def send_forget_password_email(user: User, request: Request) -> None:
    """

    Args:
        user:
        request:

    Returns:

    """
    return send_verify_email(
        view_action=EMAIL_RESET_PASSWORD_ACTION,
        email_template_html=EMAIL_RESET_PASSWORD_TEMPLATE,
        email_template_subject=EMAIL_RESET_PASSWORD_SUBJECT,
        user=user,
        request=request,
    )
