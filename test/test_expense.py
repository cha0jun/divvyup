import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

# --- Imports from your actual project ---
# Adjust these paths to match your project structure
from main import app  
from app.models import User, ExpenseGroup, Member # Import your SQLModels
from app.auth import get_current_user # Import your Auth dependency function
from app.database import SessionDep

# --- 1. Database & Test Client Setup ---

# Create an in-memory SQLite database
# connect_args={"check_same_thread": False} is needed for SQLite with FastAPI
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture(name="session")
def session_fixture():
    """
    Creates a new database session for a test, creates tables, 
    and drops them after the test finishes.
    """
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Creates a TestClient that overrides the database dependency
    to use the in-memory test session.
    """
    def get_session_override():
        return session

    app.dependency_overrides[SessionDep] = get_session_override
    client = TestClient(app)
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

