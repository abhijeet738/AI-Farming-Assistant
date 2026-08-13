import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import CurrentUser, get_current_user
from app.db.database import Base, get_db
from app.main import app

# Setup isolated test database
TEST_DB_URL = "sqlite:///./test_farming_assistant.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock user for authenticated routes
mock_user = CurrentUser(
    id="test-user-id-1234",
    email="test@farmer.com",
    role="user"
)

def override_get_current_user():
    return mock_user

# Override dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create test database tables before tests and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_farming_assistant.db"):
        os.remove("./test_farming_assistant.db")


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Fixture that provides a database session for a single test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client() -> Generator:
    """Fixture that provides a FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def bypass_rate_limiting():
    """Bypass slowapi rate limits during testing."""
    from app.core.rate_limit import limiter
    limiter.enabled = False
    yield
    limiter.enabled = True
