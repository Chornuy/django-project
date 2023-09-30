from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db.models import BooleanField, CharField, EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.users.managers import UserManager


class User(AbstractUser):
    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    email = EmailField(_("email address"), unique=True)
    is_verified = BooleanField(_("email verification"), default=False)

    username = None  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.pk})

    def update_password(self, new_password: str):
        self.password = make_password(new_password)
