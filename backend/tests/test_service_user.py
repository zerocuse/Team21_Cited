from app import app, db
from models import User
from services.user_service import create_user
import pytest
from unittest.mock import MagicMock, patch



# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    """Mock db.session so no real database is needed."""
    mock_session = MagicMock()
    monkeypatch.setattr("create_user.db.session", mock_session)
    return mock_session


@pytest.fixture
def valid_user_data():
    return {
        "username": "jdoe",
        "email_address": "jdoe@example.com",
        "membership_status": "active",
        "first_name": "John",
        "last_name": "Doe",
        "password_hash": "hashed_password_123",
    }


# ── Happy Path ─────────────────────────────────────────────────────────────────

class TestCreateUserSuccess:

    def test_returns_user_object(self, valid_user_data, mock_db):
        user = create_user(**valid_user_data)
        assert user is not None

    def test_user_has_correct_username(self, valid_user_data, mock_db):
        user = create_user(**valid_user_data)
        assert user.username == valid_user_data["username"]

    def test_user_has_correct_email(self, valid_user_data, mock_db):
        user = create_user(**valid_user_data)
        assert user.email_address == valid_user_data["email_address"]

    def test_user_has_correct_first_name(self, valid_user_data, mock_db):
        user = create_user(**valid_user_data)
        assert user.first_name == valid_user_data["first_name"]

    def test_user_has_correct_last_name(self, valid_user_data, mock_db):
        user = create_user(**valid_user_data)
        assert user.last_name == valid_user_data["last_name"]

    def test_user_has_correct_membership_status(self, valid_user_data, mock_db):
        user = create_user(**valid_user_data)
        assert user.membership_status == valid_user_data["membership_status"]

    def test_user_has_correct_password_hash(self, valid_user_data, mock_db):
        user = create_user(**valid_user_data)
        assert user.password_hash == valid_user_data["password_hash"]

    def test_db_session_add_called(self, valid_user_data, mock_db):
        user = create_user(**valid_user_data)
        mock_db.add.assert_called_once_with(user)

    def test_db_session_commit_called(self, valid_user_data, mock_db):
        create_user(**valid_user_data)
        mock_db.commit.assert_called_once()


# ── Username Validation ────────────────────────────────────────────────────────

class TestUsernameValidation:

    def test_empty_username_raises(self, valid_user_data, mock_db):
        valid_user_data["username"] = ""
        with pytest.raises(ValueError, match="Username cannot be null or empty"):
            create_user(**valid_user_data)

    def test_whitespace_only_username_raises(self, valid_user_data, mock_db):
        valid_user_data["username"] = "   "
        with pytest.raises(ValueError, match="Username cannot be null or empty"):
            create_user(**valid_user_data)

    def test_none_username_raises(self, valid_user_data, mock_db):
        valid_user_data["username"] = None
        with pytest.raises(ValueError, match="Username cannot be null or empty"):
            create_user(**valid_user_data)


# ── Email Validation ───────────────────────────────────────────────────────────

class TestEmailValidation:

    def test_empty_email_raises(self, valid_user_data, mock_db):
        valid_user_data["email_address"] = ""
        with pytest.raises(ValueError, match="Invalid email address"):
            create_user(**valid_user_data)

    def test_none_email_raises(self, valid_user_data, mock_db):
        valid_user_data["email_address"] = None
        with pytest.raises(ValueError, match="Invalid email address"):
            create_user(**valid_user_data)

    def test_email_missing_at_symbol_raises(self, valid_user_data, mock_db):
        valid_user_data["email_address"] = "invalidemail.com"
        with pytest.raises(ValueError, match="Invalid email address"):
            create_user(**valid_user_data)

    def test_email_missing_domain_raises(self, valid_user_data, mock_db):
        valid_user_data["email_address"] = "user@"
        with pytest.raises(ValueError, match="Invalid email address"):
            create_user(**valid_user_data)

    def test_email_missing_tld_raises(self, valid_user_data, mock_db):
        valid_user_data["email_address"] = "user@domain"
        with pytest.raises(ValueError, match="Invalid email address"):
            create_user(**valid_user_data)

    def test_valid_email_with_subdomain(self, valid_user_data, mock_db):
        valid_user_data["email_address"] = "user@mail.example.com"
        user = create_user(**valid_user_data)
        assert user.email_address == "user@mail.example.com"

    def test_valid_email_with_plus(self, valid_user_data, mock_db):
        valid_user_data["email_address"] = "user+tag@example.com"
        user = create_user(**valid_user_data)
        assert user.email_address == "user+tag@example.com"


# ── First Name Validation ──────────────────────────────────────────────────────

class TestFirstNameValidation:

    def test_empty_first_name_raises(self, valid_user_data, mock_db):
        valid_user_data["first_name"] = ""
        with pytest.raises(ValueError, match="First name cannot be null or empty"):
            create_user(**valid_user_data)

    def test_whitespace_only_first_name_raises(self, valid_user_data, mock_db):
        valid_user_data["first_name"] = "   "
        with pytest.raises(ValueError, match="First name cannot be null or empty"):
            create_user(**valid_user_data)

    def test_none_first_name_raises(self, valid_user_data, mock_db):
        valid_user_data["first_name"] = None
        with pytest.raises(ValueError, match="First name cannot be null or empty"):
            create_user(**valid_user_data)


# ── Last Name Validation ───────────────────────────────────────────────────────

class TestLastNameValidation:

    def test_empty_last_name_raises(self, valid_user_data, mock_db):
        valid_user_data["last_name"] = ""
        with pytest.raises(ValueError, match="Last name cannot be null or empty"):
            create_user(**valid_user_data)

    def test_whitespace_only_last_name_raises(self, valid_user_data, mock_db):
        valid_user_data["last_name"] = "   "
        with pytest.raises(ValueError, match="Last name cannot be null or empty"):
            create_user(**valid_user_data)

    def test_none_last_name_raises(self, valid_user_data, mock_db):
        valid_user_data["last_name"] = None
        with pytest.raises(ValueError, match="Last name cannot be null or empty"):
            create_user(**valid_user_data)