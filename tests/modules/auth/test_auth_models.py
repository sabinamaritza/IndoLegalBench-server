"""Unit tests for Auth database models.

Target: tests/modules/auth/test_auth_models.py
Validates:
- Table structures for User and Session (AC4, AC5)
- User-to-Session cascade relationships
- Field defaults and constraints (id default UUID, timestamps, is_active)
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.modules.auth.models import Session, User
from app.shared.database import Base
from app.shared.security import Role


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_create_user_model_defaults(db_session):
    user = User(
        email="default_test@veritask.ai",
        name="Default Test",
        role=Role.AUTHOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.is_active is True
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)
    assert user.zitadel_sub is None


def test_user_unique_email_constraint(db_session):
    user1 = User(
        email="duplicate@veritask.ai",
        name="First User",
        role=Role.VIEWER,
    )
    db_session.add(user1)
    db_session.commit()

    user2 = User(
        email="duplicate@veritask.ai",
        name="Second User",
        role=Role.AUTHOR,
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_sessions_relationship_and_cascade(db_session):
    user = User(
        email="cascade_test@veritask.ai",
        name="Cascade Test",
        role=Role.REVIEWER,
    )
    db_session.add(user)
    db_session.commit()

    now = datetime.now(UTC)
    sess1 = Session(
        user_id=user.id,
        last_activity_at=now,
        expires_at=now + timedelta(minutes=30),
    )
    sess2 = Session(
        user_id=user.id,
        last_activity_at=now,
        expires_at=now + timedelta(minutes=60),
    )
    db_session.add_all([sess1, sess2])
    db_session.commit()

    db_session.refresh(user)
    assert len(user.sessions) == 2

    db_session.delete(user)
    db_session.commit()

    remaining_sessions = db_session.query(Session).filter(Session.user_id == user.id).all()
    assert len(remaining_sessions) == 0
