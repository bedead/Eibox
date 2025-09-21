"""
Test configuration and fixtures for E2E API testing.
Sets up test client, mocks, and common test data.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime
from typing import Generator, Dict, Any

# Import the FastAPI app
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "user_id": "test_user_123",
        "account_created": "2024-01-01T00:00:00",
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123",
        "gmail_accounts": ["test@gmail.com"]
    }


@pytest.fixture
def test_login_data() -> Dict[str, str]:
    """Sample login data for testing."""
    return {
        "username": "testuser",
        "password": "testpassword123"
    }


@pytest.fixture
def test_update_data() -> Dict[str, Any]:
    """Sample update user data for testing."""
    return {
        "username": "testuser",
        "full_name": "Updated Test User",
        "auto_email_monitoring": True,
        "email_monitoring_frequency": 120,
        "email_notifications": True,
        "gmail_accounts": ["test@gmail.com", "test2@gmail.com"]
    }


@pytest.fixture
def mock_redis():
    """Mock Redis store operations."""
    with patch('app.db.redis.db_store') as mock_store:
        # Mock store methods
        mock_store.get.return_value = None
        mock_store.put.return_value = True
        mock_store.delete.return_value = True
        mock_store.setup.return_value = True
        yield mock_store


@pytest.fixture
def mock_gmail_service():
    """Mock Gmail service operations."""
    with patch('app.services.gmail.gmail_toolkit.GmailService') as mock_service:
        mock_instance = Mock()
        mock_instance.get_user_info.return_value = {
            "email": "test@gmail.com",
            "name": "Test User"
        }
        mock_service.return_value = mock_instance
        yield mock_service


@pytest.fixture
def mock_oauth_flow():
    """Mock Google OAuth flow."""
    with patch('app.api.v1.endpoints.gmail_oauth.Flow') as mock_flow, \
         patch('oauthlib.oauth2.is_secure_transport', return_value=True):
        mock_flow_instance = Mock()
        mock_flow_instance.authorization_url = Mock(return_value=("http://example.com/oauth", "test_state"))
        mock_flow_instance.credentials = Mock()
        mock_flow_instance.credentials.token = "test_access_token"
        mock_flow_instance.credentials.refresh_token = "test_refresh_token"
        mock_flow_instance.credentials.expiry = datetime.now()
        mock_flow_instance.fetch_token = Mock()
        mock_flow.from_client_config.return_value = mock_flow_instance
        yield mock_flow_instance


@pytest.fixture
def mock_google_user_info():
    """Mock Google user info API response."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            "email": "test@gmail.com",
            "name": "Test User",
            "sub": "123456789"
        }
        mock_get.return_value = mock_response
        yield mock_response


@pytest.fixture
def mock_database_operations():
    """Mock all database operations."""
    with patch('app.api.v1.endpoints.auth.ru') as mock_register, \
         patch('app.api.v1.endpoints.auth.lu') as mock_login, \
         patch('app.api.v1.endpoints.auth.uud') as mock_update, \
         patch('app.api.v1.endpoints.gmail_oauth.add_gmail_account') as mock_add_gmail, \
         patch('app.api.v1.endpoints.gmail_oauth.uud') as mock_oauth_update, \
         patch('app.db.repos.gmail.get_gmail_accounts.get_gmail_account') as mock_get_gmail, \
         patch('app.api.v1.endpoints.test.get_gmail_account') as mock_get_gmail_test:
        
        # Mock successful responses matching actual API format
        mock_register.return_value = {"success": 200, "message": "User registered successfully", "data": "{}"}
        mock_login.return_value = {"success": 200, "message": "User logged in successfully", "data": {}}
        mock_update.return_value = {"success": 200, "message": "User details updated successfully", "updated_data": {}}
        mock_oauth_update.return_value = {"success": 200, "message": "User details updated successfully", "updated_data": {}}
        mock_add_gmail.return_value = {"success": True, "message": "Gmail account added successfully"}
        mock_get_gmail.return_value = [{"email": "test@gmail.com"}]  # Returns list of GmailAccount objects for DB function
        mock_get_gmail_test.return_value = [{"email": "test@gmail.com"}]  # Returns list for test endpoint
        
        yield {
            "register": mock_register,
            "login": mock_login,
            "update": mock_update,
            "oauth_update": mock_oauth_update,
            "add_gmail": mock_add_gmail,
            "get_gmail": mock_get_gmail_test  # Use test endpoint mock for integration tests
        }


@pytest.fixture
def mock_session_operations():
    """Mock session management operations."""
    with patch('app.services.session.session_utils.init_or_get_session') as mock_init, \
         patch('app.services.session.get_session.get_session') as mock_get, \
         patch('app.services.session.delete_session.delete_session') as mock_delete:
        
        # Mock session object
        mock_session = Mock()
        mock_session.websocket = None
        mock_session.username = "testuser"
        mock_session.thread_id = "test_thread"
        
        mock_init.return_value = mock_session
        mock_get.return_value = mock_session
        mock_delete.return_value = True
        
        yield {
            "init": mock_init,
            "get": mock_get,
            "delete": mock_delete,
            "session": mock_session
        }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment with mocked dependencies."""
    with patch.dict('os.environ', {
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'GOOGLE_CLIENT_ID': 'test_client_id',
        'GOOGLE_CLIENT_SECRET': 'test_client_secret',
        'GMAIL_REDIRECT_URI': 'http://localhost:8000/v1/oauth/gmail/callback'
    }):
        yield