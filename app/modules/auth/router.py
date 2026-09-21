"""Endpoint HTTP modul auth.

PBI-1 Login aman dan manajemen akses tim.

Cakupan modul ini:
- Login SSO lewat Zitadel
- Empat peran: Author, Reviewer, Admin, Viewer
- Pembatasan aksi per peran (RBAC)
- Idle timeout sesi
- Admin mengelola anggota tim

Router hanya menerjemahkan HTTP ke pemanggilan service. Tidak ada
logika bisnis dan tidak ada query database di file ini.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session as DBSession

from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import UserCreateRequest, UserResponse, UserUpdateRoleRequest
from app.modules.auth.service import AuthService
from app.shared.database import get_db
from app.shared.security import CurrentUser, Role, get_current_user, require_roles

router = APIRouter(
    prefix="/admin/users", tags=["Admin Members"], dependencies=[Depends(require_roles(Role.ADMIN))]
)


def get_auth_service(db: DBSession = Depends(get_db)) -> AuthService:
    return AuthService(AuthRepository(db))


@router.get("", response_model=list[UserResponse])
def get_users(
    is_active: bool | None = Query(default=None), service: AuthService = Depends(get_auth_service)
):
    return service.list_users(is_active=is_active)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateRequest, service: AuthService = Depends(get_auth_service)):
    return service.create_member(payload)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_role(
    user_id: uuid.UUID,
    payload: UserUpdateRoleRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.update_member_role(user_id, payload)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    return service.deactivate_member(target_user_id=user_id, current_user=current_user)
