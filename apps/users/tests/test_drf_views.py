import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APIRequestFactory

from apps.conftest import TEST_USER_PASSWORD
from apps.users.api.services import EMAIL_VERIFICATION_ACTION, generate_uid_and_token_from_user
from apps.users.api.views import UserViewSet

User = get_user_model()


class TestUserViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    def test_get_queryset(self, user: User, api_rf: APIRequestFactory):
        view = UserViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert user in view.get_queryset()

    @pytest.mark.django_db
    def test_user_registration(self, api_client: APIClient):
        url = reverse("v1:user-register")
        email = "jonhndoe@gmail.com"
        data = {"email": email, "password": "qwerty123451", "password2": "qwerty123451"}
        response = api_client.post(url, data=data)

        # Successfully create user
        assert 201 == response.status_code

    @pytest.mark.django_db
    def test_verification_email(self, api_client: APIClient):
        url = reverse("v1:user-register")
        email = "jonhndoe@gmail.com"
        data = {"email": email, "password": "qwerty123451", "password2": "qwerty123451"}

        response = api_client.post(url, data=data)
        # Successfully create user
        assert status.HTTP_201_CREATED == response.status_code

        user = User.objects.get(email="jonhndoe@gmail.com")

        #  Generate verification link
        verification_params = generate_uid_and_token_from_user(user)
        verification_link = reverse(EMAIL_VERIFICATION_ACTION, kwargs=verification_params)

        assert user.email == email
        assert user.is_verified is False

        # Check that email was send
        assert len(mail.outbox) == 1
        assert verification_link in mail.outbox[0].body

        # Detect that we send verification email
        response = api_client.get(verification_link)

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.is_verified is True

    @pytest.mark.django_db
    def test_change_password(self, user: User, api_client: APIClient):
        url = reverse("v1:user-change-password")
        login_url = reverse("v1:auth-token")

        response = api_client.post(login_url, data={"email": user.email, "password": TEST_USER_PASSWORD})
        assert response.status_code == status.HTTP_200_OK

        access_token = response.data["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        response = api_client.post(
            url, data={"current_password": TEST_USER_PASSWORD, "password": "cGf!9Wj2O*36", "password2": "cGf!9Wj2O*36"}
        )
        print(response.data)
