from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class TokenObtainPairSerializerIfUserVerified(TokenObtainPairSerializer):
    """Override serializer for Obtaining the token.
    To obtain token user must verify email first
    """

    def validate(self, attrs: dict) -> dict:
        """Override validation for obtaining user token.
        Before validating email and password user in DB, check if user verify email after registration
        Args:
            attrs:

        Returns:

        """
        data = super().validate(attrs)
        if not self.user.is_verified:
            raise ValidationError(_("Please verify email first"))

        return data
