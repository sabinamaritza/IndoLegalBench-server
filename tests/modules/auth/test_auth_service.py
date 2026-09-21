"""Unit tests for AuthService business logic.

Validates:
- list_users (with and without is_active filter)
- create_member (success, conflict 409, unregistered Zitadel 422)
- update_member_role (success, not found 404)
- deactivate_member (success, self-deactivation 422, not found 404)
"""

import uuid
from unittest.mock import MagicMock
import pytest

from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import UserCreateRequest, UserUpdateRoleRequest
from app.modules.auth.service import AuthService
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError
from app.shared.security import CurrentUser, Role


@pytest.fixture
def mock_repo():
    return MagicMock(spec=AuthRepository)


@pytest.fixture
def auth_service(mock_repo):
    return AuthService(mock_repo)


@pytest.fixture
def current_admin():
    return CurrentUser(
        user_id="11111111-1111-1111-1111-111111111111",
        email="admin@veritask.ai",
        role=Role.ADMIN,
    )


@pytest.fixture
def dummy_user():
    return User(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        email="user@veritask.ai",
        name="User Veritask",
        role=Role.AUTHOR,
        is_active=True,
    )


def test_service_list_users(auth_service, mock_repo, dummy_user):
    mock_repo.get_users.return_value = [dummy_user]

    res_all = auth_service.list_users()
    assert res_all == [dummy_user]
    mock_repo.get_users.assert_called_with(is_active=None)

    res_active = auth_service.list_users(is_active=True)
    assert res_active == [dummy_user]
    mock_repo.get_users.assert_called_with(is_active=True)


def test_service_create_member_success(auth_service, mock_repo, dummy_user):
    mock_repo.get_user_by_email.return_value = None
    mock_repo.create_user.return_value = dummy_user

    payload = UserCreateRequest(
        email="user@veritask.ai",
        name="User Veritask",
        role=Role.AUTHOR,
    )
    res = auth_service.create_member(payload)

    assert res == dummy_user
    mock_repo.create_user.assert_called_once_with(
        name="User Veritask",
        email="user@veritask.ai",
        role=Role.AUTHOR,
        zitadel_sub="zitadel_sub_user@veritask.ai",
    )


def test_service_create_member_email_conflict(auth_service, mock_repo, dummy_user):
    mock_repo.get_user_by_email.return_value = dummy_user

    payload = UserCreateRequest(
        email="user@veritask.ai",
        name="User Duplicate",
        role=Role.AUTHOR,
    )
    with pytest.raises(ConflictError) as exc_info:
        auth_service.create_member(payload)

    assert "already exists" in str(exc_info.value)
    mock_repo.create_user.assert_not_called()


def test_service_create_member_unregistered_zitadel(auth_service, mock_repo):
    mock_repo.get_user_by_email.return_value = None

    payload = UserCreateRequest(
        email="unregistered@veritask.ai",
        name="Ghost User",
        role=Role.VIEWER,
    )
    with pytest.raises(ValidationError) as exc_info:
        auth_service.create_member(payload)

    assert "Zitadel" in str(exc_info.value)
    mock_repo.create_user.assert_not_called()


def test_service_update_member_role_success(auth_service, mock_repo, dummy_user):
    mock_repo.get_user_by_id.return_value = dummy_user
    mock_repo.update_user_role.return_value = dummy_user

    payload = UserUpdateRoleRequest(role=Role.REVIEWER)
    res = auth_service.update_member_role(dummy_user.id, payload)

    assert res == dummy_user
    mock_repo.update_user_role.assert_called_once_with(dummy_user, Role.REVIEWER)


def test_service_update_member_role_not_found(auth_service, mock_repo):
    mock_repo.get_user_by_id.return_value = None
    target_id = uuid.uuid4()

    payload = UserUpdateRoleRequest(role=Role.REVIEWER)
    with pytest.raises(NotFoundError):
        auth_service.update_member_role(target_id, payload)


def test_service_deactivate_member_success(auth_service, mock_repo, dummy_user, current_admin):
    mock_repo.get_user_by_id.return_value = dummy_user
    mock_repo.deactivate_user.return_value = dummy_user

    res = auth_service.deactivate_member(dummy_user.id, current_admin)

    assert res == dummy_user
    mock_repo.delete_sessions_by_user_id.assert_called_once_with(dummy_user.id)
    mock_repo.deactivate_user.assert_called_once_with(dummy_user)


def test_service_deactivate_self_fails(auth_service, mock_repo, current_admin):
    admin_uuid = uuid.UUID(current_admin.user_id)

    with pytest.raises(ValidationError) as exc_info:
        auth_service.deactivate_member(admin_uuid, current_admin)

    assert exc_info.value.code == "CANNOT_DEACTIVATE_SELF"
    mock_repo.delete_sessions_by_user_id.assert_not_called()


def test_service_deactivate_member_not_found(auth_service, mock_repo, current_admin):
    mock_repo.get_user_by_id.return_value = None
    target_id = uuid.uuid4()

    with pytest.raises(NotFoundError):
        auth_service.deactivate_member(target_id, current_admin)