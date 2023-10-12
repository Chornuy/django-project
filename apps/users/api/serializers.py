from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.base.serializers.fields import CurrentUserPasswordField, PasswordField
from apps.users.api.services import send_verification_email_after_registration
from apps.users.api.validators import FieldMatchValidator

User = get_user_model()


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


class RegisterUserSerializer(PasswordMatchMixin, serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message=_("This email already registered"))],
        max_length=256,
        required=True,
        allow_null=False,
    )

    def create(self, validated_data):
        del validated_data["password2"]

        user = User.objects.create_user(**validated_data)
        send_verification_email_after_registration(user, request=self.context["request"])
        return user

    class Meta:
        model = User
        fields = ["email"] + PasswordMatchMixin.Meta.fields

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }
        validators = PasswordMatchMixin.Meta.validators


class ResetPasswordSerializer(PasswordMatchMixin, serializers.ModelSerializer):
    def update(self, instance: User, validated_data: dict):
        instance.update_password(validated_data["password"])
        instance.save()
        return instance

    class Meta:
        model = User
        fields = PasswordMatchMixin.Meta.fields
        validators = PasswordMatchMixin.Meta.validators
        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }


class ChangeCurrentPasswordSerializer(PasswordMatchMixin, serializers.ModelSerializer):
    current_password = CurrentUserPasswordField()

    def update(self, instance: User, validated_data: dict):
        instance.update_password(validated_data["password"])
        instance.save()
        return instance

    class Meta:
        model = User
        fields = PasswordMatchMixin.Meta.fields + ["current_password"]
        validators = PasswordMatchMixin.Meta.validators + [
            FieldMatchValidator("current_password", "password", should_match=False, error_code="password_match")
        ]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }
