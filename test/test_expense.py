import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool # <--- IMPORTANT IMPORT
from fastapi.testclient import TestClient

from app.models import User, ExpenseGroup, Member, Expense, Payment, Invitation, Breakdown
from main import app
from app.database import SessionDep
from app.auth import get_current_user

# 2. Use StaticPool for SQLite Memory
# This ensures that multiple threads (FastAPI) and the Test Runner share 
# the SAME in-memory database instance.
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool # <--- THIS IS CRITICAL FOR IN-MEMORY TESTS
)

@pytest.fixture(name="session")
def session_fixture():
    """
    Creates a new database session for a test. 
    """
    # Create the tables in the specific in-memory engine
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session
    
    # Clean up after test
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Returns a TestClient with the database dependency overridden.
    """
    def get_session_override():
        return session

    app.dependency_overrides[SessionDep] = get_session_override
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

# --- 2. Data Seeding Fixtures ---

@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """
    Creates a valid User in the database.
    """
    user = User(
        name="Test User", 
        email="test@example.com", 
        password_hash="hashed_secret_password" # Matches your 'password_hash' field
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="test_group")
def test_group_fixture(session: Session, test_user: User):
    """
    Creates an ExpenseGroup and adds the 'test_user' as a Member.
    """
    # 1. Create the Group
    # Note: Your model requires admin_id, created_by, and modified_by.
    # We use the test_user's ID for all of these for simplicity.
    group = ExpenseGroup(
        name="Trip to Vegas",
        description="Casino and Food",
        admin_id=test_user.id,      # Required FK
        created_by=test_user.id,    # Required FK
        modified_by=test_user.id    # Required FK
    )
    session.add(group)
    session.commit()
    session.refresh(group)
    
    # 2. Create the Membership
    # Your Member model links user and group. 
    # 'added_by' is optional, so we leave it None for the creator.
    member = Member(
        user_id=test_user.id,
        expense_group_id=group.id,
        added_by=None 
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    
    return group

@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, test_user: User):
    """
    Returns a TestClient where the user is already 'logged in'.
    It overrides the 'get_current_user' dependency.
    """
    # Ensure this import matches your actual auth dependency
    app.dependency_overrides[get_current_user] = lambda: test_user
    return client

# --- 3. The Tests ---

def test_get_expenses_empty(auth_client, test_group):
    """Test getting expenses when none exist."""
    response = auth_client.get(f"/api/expenses/{test_group.id}")
    assert response.status_code == 200
    
def test_get_expense_empty(auth_client, test_group):
    """Test getting an expense it doesn't exist."""
    expense_id = 0
    response = auth_client.get(f"/api/expenses/{expense_id}/groups/{test_group.id}")
    assert response.status_code == 404

