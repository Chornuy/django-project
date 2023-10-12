import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.conftest import TEST_USER_PASSWORD
from apps.test_utils.api_client import JwtAPIClient

User = get_user_model()


class TestUserViewSet:
    @pytest.fixture
    def api_client(self) -> JwtAPIClient:
        return JwtAPIClient()

    @pytest.mark.django_db
    def test_login_flow(self, user: User, api_client: JwtAPIClient):
        response = api_client.jwt_login(email=user.email, password=TEST_USER_PASSWORD)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data.keys()
        assert "refresh" in response.data.keys()
