from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient


class JwtAPIClient(APIClient):
    login_action = reverse("v1:auth-token")
    logout_action = reverse("v1:auth-logout")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def jwt_login(self, email: str, password: str):
        """Helper function for login in system for tests

        Args:
            email (str): email for test user
            password (str): password for test user

        Returns:
            None
        """
        response = self.post(self.login_action, data={"email": email, "password": password})
        if response.status_code != status.HTTP_200_OK:
            return response

        self.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response

    def jwt_logout(self) -> None:
        """Helper method. Call logout url in system

        Returns:
            None
        """
        self.get(self.logout_action)
        super().logout()
