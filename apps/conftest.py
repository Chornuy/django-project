import pytest

from apps.test_utils.factories import UserFactory
from apps.users.models import User

TEST_USER_PASSWORD = "56&E8b8Xq3Yz"


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user_factory(db) -> type[UserFactory]:
    return UserFactory


@pytest.fixture
def user(db) -> User:
    return UserFactory(password=TEST_USER_PASSWORD)


@pytest.fixture
def user_vasya(db) -> User:
    return UserFactory(email="vasya@gmail", password=TEST_USER_PASSWORD)
