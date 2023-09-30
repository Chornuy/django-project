from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.base.api.views import ApiGenericViewSet
from apps.core.constants import HttpMethods
from apps.users.api.serializers import ChangeCurrentPasswordSerializer, RegisterUserSerializer, ResetPasswordSerializer
from apps.users.api.services import send_forget_password_email
from apps.users.api.throttling import EmailVerifyAndPasswordResetRateThrottle

User = get_user_model()


class UserViewSet(ApiGenericViewSet):
    """User view set that represents common actions for basic user actions.
    Like: registration, verification, and password reset
    """

    queryset = User.objects.all()

    messages = {
        "verification_successful": _("Email successful verified"),
        "password_change_successful": _("Password changed successful"),
        "password_change_link_send": _("Reset link was send to user email"),
        "new_password_set": _("New password set successful"),
        "user_registered": _("User registered. Please verify user through email"),
    }

    @action(methods=[HttpMethods.GET], detail=False)
    def ping(self, request):
        return Response(data="pong")

    @staticmethod
    def get_user_by_token_and_uid(uid64: str, token: str) -> User:
        """Helper function to get user by uid and validate token.

        Args:
            uid64 (str): uid64 hashed for user id
            token (str): temporary token for verification purpose

        Raises:
            ValueError: in case if no such user found in db or not valid token

        Returns:
            User: object of User model
        """
        try:
            user = User.objects.get_by_uid(pk=uid64)
        except User.DoesNotExist:
            raise ValidationError(_("Verify token is invalid"))

        if not default_token_generator.check_token(user, token):
            raise ValidationError(_("Verify token is invalid"))

        return user

    def perform_serializer_save(self, *args, **kwargs):
        """Small helper function for custom action in ViewSet.
        Proxy data from view to serializer_class, validate data and perform save() method.

        Args:
            *args (list): Argument that proxy to Serializer class in __init__ method
            **kwargs (dict): Key Arguments that proxy to Serializer class in __init__ method

        Returns:
            Serializer: object of serializer after validation and performing save action

        """
        serializer = self.get_serializer(*args, **kwargs)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer

    @action(methods=[HttpMethods.POST], detail=False, serializer_class=RegisterUserSerializer)
    def register(self, request):
        """Register a new user for the system

        Args:
            request: (Request) Django request object

        Returns:
            Response: response with status code 201 in case user successfully was created
        """
        serializer = self.perform_serializer_save(data=request.data)
        return self.create_successful_response(
            data=serializer.data, status_code=status.HTTP_201_CREATED, message_code="user_registered"
        )

    @action(methods=[HttpMethods.GET], detail=False, url_path=r"verify/(?P<uid64>[0-9A-Za-z]+)-(?P<token>.+)")
    def verify(self, request, uid64, token):
        """Method verify user email. Verification url send on registration phase, on user email.

        Args:
            request (Request): Django request object
            uid64 (str): Hashed user id from db
            token (str): temporary token for user verification

        Returns:
            Response: Django Response object
        """
        user = self.get_user_by_token_and_uid(uid64, token)
        user.is_verified = True
        user.save()

        return self.create_successful_response(status_code=status.HTTP_200_OK, message_code="verification_successful")

    @action(
        methods=[HttpMethods.GET],
        detail=False,
        lookup_field="email",
        lookup_url_kwarg="email",
        throttle_classes=[EmailVerifyAndPasswordResetRateThrottle],
    )
    def resend_verify(self, request):
        pass

    @action(
        methods=[HttpMethods.GET],
        detail=False,
        lookup_field="email",
        lookup_url_kwarg="email",
        url_path=r"forget-password/(?P<email>[\w\.]+@([\w-]+\.)+[\w-]{2,4})",
        throttle_classes=[EmailVerifyAndPasswordResetRateThrottle],
    )
    def forget_password(self, request, email):
        """Forget password action.
        Public api call. Find user by email and send reset verification url.

        Args:
            request (Request): Django request object
            email (str): User email to reset the password

        Returns:
            Response: Django Response object

        """
        user = self.get_object()
        send_forget_password_email(user, request)
        return self.create_successful_response(
            status_code=status.HTTP_200_OK, message_code="password_change_link_send"
        )

    @action(
        methods=[HttpMethods.POST],
        detail=False,
        serializer_class=ResetPasswordSerializer,
        url_path=r"set-new-password/(?P<uid64>[0-9A-Za-z]+)-(?P<token>.+)",
    )
    def set_new_password(self, request, uid64, token):
        """Set up a new password by verification link that was sent in forgot-password action.

        Args:
            request (Request): Django request object
            uid64 (str): Hashed user id
            token (str): Temporary token for verification of action

        Returns:
            Response: Django response
        """
        user = self.get_user_by_token_and_uid(uid64, token)
        self.perform_serializer_save(instance=user, data=request.data)
        return self.create_successful_response(status_code=status.HTTP_200_OK, message_code="new_password_set")

    @action(
        methods=[HttpMethods.POST],
        detail=False,
        serializer_class=ChangeCurrentPasswordSerializer,
        permission_classes=[IsAuthenticated],
        url_path=r"change-password/",
    )
    def change_password(self, request):
        """Change password for user.
        Work only for logged-in Users

        Args:
            request (Request): Django request object

        Returns:
            Response: Django Response object

        """
        self.perform_serializer_save(instance=request.user, data=request.data)
        return self.create_successful_response(
            status_code=status.HTTP_200_OK, message_code="password_change_successful"
        )
