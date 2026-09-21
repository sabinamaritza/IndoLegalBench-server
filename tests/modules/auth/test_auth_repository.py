"""Unit tests for AuthRepository data access using SQLite in-memory.

Validates:
- get_users (unfiltered and is_active filter)
- get_user_by_id and get_user_by_email
- create_user
- update_user_role
- deactivate_user
- delete_sessions_by_user_id
"""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.auth.models import Session
from app.modules.auth.repository import AuthRepository
from app.shared.database import Base
from app.shared.security import Role


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def repo(in_memory_db):
    return AuthRepository(in_memory_db)


def test_repo_create_and_get_user(repo):
    user = repo.create_user(
        name="Alice Author",
        email="alice@veritask.ai",
        role=Role.AUTHOR,
        zitadel_sub="sub_alice",
    )

    assert user.id is not None
    assert user.name == "Alice Author"
    assert user.email == "alice@veritask.ai"
    assert user.role == Role.AUTHOR
    assert user.is_active is True

    fetched_by_id = repo.get_user_by_id(user.id)
    assert fetched_by_id is not None
    assert fetched_by_id.email == "alice@veritask.ai"

    fetched_by_email = repo.get_user_by_email("alice@veritask.ai")
    assert fetched_by_email is not None
    assert fetched_by_email.id == user.id

    assert repo.get_user_by_email("nonexistent@veritask.ai") is None


def test_repo_get_users_filtering(repo):
    user1 = repo.create_user("User One", "one@veritask.ai", Role.AUTHOR, "sub1")
    user2 = repo.create_user("User Two", "two@veritask.ai", Role.REVIEWER, "sub2")
    repo.deactivate_user(user2)

    all_users = repo.get_users()
    assert len(all_users) == 2

    active_users = repo.get_users(is_active=True)
    assert len(active_users) == 1
    assert active_users[0].id == user1.id

    inactive_users = repo.get_users(is_active=False)
    assert len(inactive_users) == 1
    assert inactive_users[0].id == user2.id


def test_repo_update_user_role(repo):
    user = repo.create_user("Bob", "bob@veritask.ai", Role.VIEWER, "sub_bob")
    updated_user = repo.update_user_role(user, Role.ADMIN)

    assert updated_user.role == Role.ADMIN
    assert repo.get_user_by_id(user.id).role == Role.ADMIN


def test_repo_deactivate_and_delete_sessions(repo, in_memory_db):
    user = repo.create_user(
        "Charlie", "charlie@veritask.ai", Role.AUTHOR, "sub_charlie"
    )

    now = datetime.now(timezone.utc)
    session1 = Session(
        user_id=user.id,
        expires_at=now + timedelta(hours=1),
    )
    session2 = Session(
        user_id=user.id,
        expires_at=now + timedelta(hours=2),
    )
    in_memory_db.add_all([session1, session2])
    in_memory_db.commit()

    assert in_memory_db.query(Session).filter(Session.user_id == user.id).count() == 2

    deactivated = repo.deactivate_user(user)
    assert deactivated.is_active is False

    deleted_count = repo.delete_sessions_by_user_id(user.id)
    assert deleted_count == 2
    assert in_memory_db.query(Session).filter(Session.user_id == user.id).count() == 0