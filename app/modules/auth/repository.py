"""Akses database modul auth.

ATURAN: hanya auth/service.py yang boleh memanggil file ini. Modul lain
tidak boleh mengimpor repository milik modul lain.

Isi file ini murni query, tanpa logika bisnis.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.auth.models import User, UserSession
from app.shared.security import Role


def get_user_by_sub(db: Session, zitadel_sub: str) -> User | None:
    return db.query(User).filter(User.zitadel_sub == zitadel_sub).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_users(db: Session, is_active: bool | None = None) -> list[User]:
    query = db.query(User)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.all()


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    role: Role,
    zitadel_sub: str | None = None,
) -> User:
    user = User(
        name=name,
        email=email,
        role=role,
        zitadel_sub=zitadel_sub,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_role(db: Session, user: User, role: Role) -> User:
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def update_user_profile(
    db: Session,
    user: User,
    *,
    name: str | None,
    email: str | None,
    now: datetime | None = None,
) -> User:
    # TODO(SCRUM-89): directory of record is the users table, not IdP
    if not name and not email:
        return user
    if name:
        user.name = name
    if email:
        user.email = email
    user.updated_at = now or datetime.now(UTC)
    db.commit()
    db.refresh(user)
    return user


def assign_zitadel_sub(
    db: Session, user: User, zitadel_sub: str, *, now: datetime | None = None
) -> User:
    user.zitadel_sub = zitadel_sub
    user.updated_at = now or datetime.now(UTC)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user: User) -> User:
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


def create_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    expires_at: datetime,
    zitadel_sid: str | None = None,
    id_token: str | None = None,
    now: datetime | None = None,
) -> UserSession:
    stamp = now or datetime.now(UTC)
    session = UserSession(
        user_id=user_id,
        created_at=stamp,
        last_activity_at=stamp,
        expires_at=expires_at,
        zitadel_sid=zitadel_sid,
        id_token=id_token,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: uuid.UUID) -> UserSession | None:
    return db.get(UserSession, session_id)


def delete_session(db: Session, session_id: uuid.UUID) -> None:
    session = db.get(UserSession, session_id)
    if session is None:
        return
    db.delete(session)
    db.commit()


def delete_sessions_by_user_id(db: Session, user_id: uuid.UUID) -> int:
    deleted_count = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted_count


def update_session_activity(
    db: Session,
    session: UserSession,
    *,
    last_activity_at: datetime,
) -> UserSession:
    session.last_activity_at = last_activity_at
    db.commit()
    db.refresh(session)
    return session
