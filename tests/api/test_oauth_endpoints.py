"""
E2E tests for Gmail OAuth endpoints.
Tests OAuth flow initiation, callback handling, and status checking.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from typing import Dict, Any
from datetime import datetime, timedelta


class TestOAuthEndpoints:
    """Test suite for Gmail OAuth endpoints."""

    def test_gmail_oauth_start_success(
        self, 
        client: TestClient, 
        mock_oauth_flow: Mock,
        mock_redis
    ):
        """Test successful Gmail OAuth flow initiation."""
        params = {
            "username": "testuser",
            "mobile_session_id": "test_session_123"
        }
        
        response = client.get("/v1/oauth/gmail/start", params=params, follow_redirects=False)
        
        # Should redirect to OAuth URL
        assert response.status_code == 307  # Redirect status
        assert "oauth" in response.headers["location"].lower()


    def test_gmail_oauth_start_missing_username(self, client: TestClient):
        """Test Gmail OAuth start without username."""
        params = {"mobile_session_id": "test_session_123"}
        
        response = client.get("/v1/oauth/gmail/start", params=params)
        
        assert response.status_code == 422  # Missing required parameter


    def test_gmail_oauth_start_missing_session_id(self, client: TestClient):
        """Test Gmail OAuth start without mobile session ID."""
        params = {"username": "testuser"}
        
        response = client.get("/v1/oauth/gmail/start", params=params)
        
        assert response.status_code == 422  # Missing required parameter


    def test_gmail_oauth_callback_success(
        self, 
        client: TestClient,
        mock_oauth_flow: Mock,
        mock_google_user_info: Mock,
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test successful Gmail OAuth callback."""
        # First, simulate starting OAuth flow to create state
        with patch('app.api.v1.endpoints.gmail_oauth.oauth_states') as mock_states:
            test_state = "test_state_123"
            mock_states.__contains__ = Mock(return_value=True)
            mock_states.__getitem__ = Mock(return_value={
                "username": "testuser",
                "mobile_session_id": "test_session_123",
                "timestamp": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=5),
                "completed": False
            })
            mock_states.__setitem__ = Mock()
            
            # Mock the OAuth flow fetch_token method
            mock_oauth_flow.fetch_token = Mock()
            
            params = {
                "state": test_state,
                "code": "test_auth_code"
            }
            
            response = client.get("/v1/oauth/gmail/callback", params=params)
            
            assert response.status_code == 200
            assert "connected" in response.text.lower()
            
            # Verify database operations were called
            mock_database_operations["add_gmail"].assert_called_once()
            mock_database_operations["oauth_update"].assert_called_once()


    def test_gmail_oauth_callback_invalid_state(self, client: TestClient):
        """Test Gmail OAuth callback with invalid state."""
        params = {
            "state": "invalid_state",
            "code": "test_auth_code"
        }
        
        response = client.get("/v1/oauth/gmail/callback", params=params)
        
        assert response.status_code == 200  # Returns HTML error page
        assert "error" in response.text.lower()


    def test_gmail_oauth_callback_expired_state(
        self, 
        client: TestClient,
        mock_redis
    ):
        """Test Gmail OAuth callback with expired state."""
        with patch('app.api.v1.endpoints.gmail_oauth.oauth_states') as mock_states:
            test_state = "expired_state_123"
            mock_states.__contains__ = Mock(return_value=True)
            mock_states.__getitem__ = Mock(return_value={
                "username": "testuser",
                "mobile_session_id": "test_session_123",
                "timestamp": datetime.now() - timedelta(minutes=15),
                "expires_at": datetime.now() - timedelta(minutes=5),  # Expired
                "completed": False
            })
            mock_states.__delitem__ = Mock()
            
            params = {
                "state": test_state,
                "code": "test_auth_code"
            }
            
            response = client.get("/v1/oauth/gmail/callback", params=params)
            
            assert response.status_code == 200
            assert "expired" in response.text.lower()


    def test_gmail_oauth_callback_database_error(
        self, 
        client: TestClient,
        mock_oauth_flow: Mock,
        mock_google_user_info: Mock,
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test Gmail OAuth callback with database save error."""
        # Mock database error
        mock_database_operations["add_gmail"].return_value = {
            "success": False,
            "error": "Database connection failed"
        }
        
        with patch('app.api.v1.endpoints.gmail_oauth.oauth_states') as mock_states:
            test_state = "test_state_123"
            mock_states.__contains__ = Mock(return_value=True)
            mock_states.__getitem__ = Mock(return_value={
                "username": "testuser",
                "mobile_session_id": "test_session_123",
                "timestamp": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=5),
                "completed": False
            })
            
            mock_oauth_flow.fetch_token = Mock()
            
            params = {
                "state": test_state,
                "code": "test_auth_code"
            }
            
            response = client.get("/v1/oauth/gmail/callback", params=params)
            
            assert response.status_code == 200
            assert "failed to save" in response.text.lower()


    def test_check_oauth_status_completed(
        self, 
        client: TestClient,
        mock_redis
    ):
        """Test checking OAuth status when completed."""
        mobile_session_id = "test_session_123"
        
        with patch('app.api.v1.endpoints.gmail_oauth.oauth_states') as mock_states:
            # Mock completed OAuth state
            mock_states.items.return_value = [
                ("state_123", {
                    "mobile_session_id": mobile_session_id,
                    "completed": True,
                    "email": "test@gmail.com"
                })
            ]
            mock_states.__delitem__ = Mock()
            
            response = client.get(f"/v1/oauth/gmail/status/{mobile_session_id}")
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["completed"] is True
            assert response_data["email"] == "test@gmail.com"


    def test_check_oauth_status_not_completed(
        self, 
        client: TestClient,
        mock_redis
    ):
        """Test checking OAuth status when not completed."""
        mobile_session_id = "test_session_123"
        
        with patch('app.api.v1.endpoints.gmail_oauth.oauth_states') as mock_states:
            # Mock incomplete OAuth state
            mock_states.items.return_value = [
                ("state_123", {
                    "mobile_session_id": mobile_session_id,
                    "completed": False,
                    "email": ""
                })
            ]
            
            response = client.get(f"/v1/oauth/gmail/status/{mobile_session_id}")
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["completed"] is False


    def test_check_oauth_status_not_found(
        self, 
        client: TestClient,
        mock_redis
    ):
        """Test checking OAuth status for non-existent session."""
        mobile_session_id = "nonexistent_session"
        
        with patch('app.api.v1.endpoints.gmail_oauth.oauth_states') as mock_states:
            # Mock empty OAuth states
            mock_states.items.return_value = []
            
            response = client.get(f"/v1/oauth/gmail/status/{mobile_session_id}")
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["completed"] is False


    def test_oauth_integration_flow(
        self, 
        client: TestClient,
        mock_oauth_flow: Mock,
        mock_google_user_info: Mock,
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test complete OAuth integration flow."""
        mobile_session_id = "integration_test_session"
        username = "testuser"
        
        # 1. Start OAuth flow
        start_params = {
            "username": username,
            "mobile_session_id": mobile_session_id
        }
        
        start_response = client.get("/v1/oauth/gmail/start", params=start_params, follow_redirects=False)
        assert start_response.status_code == 307  # Redirect
        
        # 2. Simulate successful callback (mocked)
        with patch('app.api.v1.endpoints.gmail_oauth.oauth_states') as mock_states:
            test_state = "integration_state_123"
            mock_states.__contains__ = Mock(return_value=True)
            mock_states.__getitem__ = Mock(return_value={
                "username": username,
                "mobile_session_id": mobile_session_id,
                "timestamp": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=5),
                "completed": False
            })
            mock_states.__setitem__ = Mock()
            
            mock_oauth_flow.fetch_token = Mock()
            
            callback_params = {
                "state": test_state,
                "code": "integration_auth_code"
            }
            
            callback_response = client.get("/v1/oauth/gmail/callback", params=callback_params)
            assert callback_response.status_code == 200
            
            # 3. Check status should show completion
            mock_states.items.return_value = [
                (test_state, {
                    "mobile_session_id": mobile_session_id,
                    "completed": True,
                    "email": "test@gmail.com"
                })
            ]
            mock_states.__delitem__ = Mock()
            
            status_response = client.get(f"/v1/oauth/gmail/status/{mobile_session_id}")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            assert status_data["completed"] is True
            assert status_data["email"] == "test@gmail.com"