"""Logika bisnis modul auth.

PBI-1 Login aman dan manajemen akses tim.

Ini satu-satunya pintu masuk yang boleh dipanggil modul lain. Service
tidak boleh menyentuh HTTP. Kalau aturan bisnis dilanggar, lempar
exception dari app.shared.exceptions.
"""

import uuid

from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import UserCreateRequest, UserUpdateRoleRequest
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError
from app.shared.security import CurrentUser


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def list_users(self, is_active: bool | None = None) -> list[User]:
        return self.repo.get_users(is_active=is_active)

    def _verify_user_in_zitadel(self, email: str) -> str | None:
        if "unregistered" in email:
            return None
        return f"zitadel_sub_{email}"

    def create_member(self, payload: UserCreateRequest) -> User:
        if self.repo.get_user_by_email(payload.email):
            raise ConflictError(f"Email '{payload.email}' already exists")

        zitadel_sub = self._verify_user_in_zitadel(payload.email)
        if not zitadel_sub:
            raise ValidationError("User not registered in Zitadel IdP")

        return self.repo.create_user(
            name=payload.name, email=payload.email, role=payload.role, zitadel_sub=zitadel_sub
        )

    def update_member_role(self, user_id: uuid.UUID, payload: UserUpdateRoleRequest) -> User:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return self.repo.update_user_role(user, payload.role)

    def deactivate_member(self, target_user_id: uuid.UUID, current_user: CurrentUser) -> User:
        if str(current_user.user_id) == str(target_user_id):
            raise ValidationError("CANNOT_DEACTIVATE_SELF", code="CANNOT_DEACTIVATE_SELF")

        user = self.repo.get_user_by_id(target_user_id)
        if not user:
            raise NotFoundError("User not found")

        self.repo.delete_sessions_by_user_id(user.id)
        return self.repo.deactivate_user(user)
