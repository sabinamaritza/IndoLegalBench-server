"""Tabel database milik modul auth.

ATURAN: file ini hanya boleh diimpor dari dalam app/modules/auth/.

Semua model wajib mewarisi Base dari app.shared.database supaya
terdeteksi Alembic.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.shared.database import Base
from app.shared.security import Role


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zitadel_sub = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(Enum(Role, name="user_role_enum"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    last_activity_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = relationship("User", back_populates="sessions")
