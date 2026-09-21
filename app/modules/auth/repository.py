"""Akses database modul auth.

ATURAN: hanya auth/service.py yang boleh memanggil file ini. Modul lain
tidak boleh mengimpor repository milik modul lain.

Isi file ini murni query, tanpa logika bisnis.
"""

import uuid

from sqlalchemy.orm import Session as DBSession

from app.modules.auth.models import Session, User
from app.shared.security import Role


class AuthRepository:
    def __init__(self, db: DBSession):
        self.db = db

    def get_users(self, is_active: bool | None = None) -> list[User]:
        query = self.db.query(User)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        return query.all()

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, name: str, email: str, role: Role, zitadel_sub: str) -> User:
        user = User(name=name, email=email, role=role, zitadel_sub=zitadel_sub, is_active=True)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user_role(self, user: User, role: Role) -> User:
        user.role = role
        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate_user(self, user: User) -> User:
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_sessions_by_user_id(self, user_id: uuid.UUID) -> int:
        deleted_count = (
            self.db.query(Session)
            .filter(Session.user_id == user_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted_count
