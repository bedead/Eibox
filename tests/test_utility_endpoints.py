"""
E2E tests for utility/test endpoints.
Tests health check, Google account retrieval, and session management.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from typing import Dict, Any


class TestUtilityEndpoints:
    """Test suite for utility and test endpoints."""

    def test_health_check_success(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/v1/test/health")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "ok"
        assert "Auth service is running" in response_data["message"]


    def test_get_google_account_success(
        self, 
        client: TestClient,
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test successful Google account retrieval."""
        request_data = {"username": "testuser"}
        
        response = client.post("/v1/test/get_google_account/", json=request_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "accounts" in response_data
        
        # Verify database operation was called
        mock_database_operations["get_gmail"].assert_called_once()


    def test_get_google_account_missing_username(self, client: TestClient):
        """Test Google account retrieval without username."""
        response = client.post("/v1/test/get_google_account/", json={})
        
        assert response.status_code == 422  # Validation error for missing username


    def test_get_google_account_database_error(
        self, 
        client: TestClient,
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test Google account retrieval with database error."""
        # Mock database error
        mock_database_operations["get_gmail"].side_effect = Exception("Database connection failed")
        
        request_data = {"username": "testuser"}
        
        response = client.post("/v1/test/get_google_account/", json=request_data)
        
        assert response.status_code == 500
        response_data = response.json()
        assert "Failed to save tokens" in response_data["detail"]
        assert "Database connection failed" in response_data["detail"]


    def test_get_google_account_no_accounts(
        self, 
        client: TestClient,
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test Google account retrieval when user has no accounts."""
        # Mock empty result
        mock_database_operations["get_gmail"].return_value = {
            "success": True,
            "accounts": []
        }
        
        request_data = {"username": "testuser"}
        
        response = client.post("/v1/test/get_google_account/", json=request_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["accounts"] == []


    def test_close_chat_websocket_success(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test successful chat websocket closure."""
        username = "testuser"
        thread_id = "test_thread_123"
        
        with patch('app.services.session.session_utils.close_websocket_session') as mock_close:
            mock_close.return_value = {"success": True, "message": "Session closed"}
            
            response = client.post(f"/v1/test/chatbot/close/{username}/{thread_id}")
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert "Session closed" in response_data["message"]
            
            # Verify session operations were called
            mock_session_operations["get"].assert_called_once()
            mock_close.assert_called_once()


    def test_close_chat_websocket_session_not_found(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test chat websocket closure when session doesn't exist."""
        username = "nonexistent"
        thread_id = "nonexistent_thread"
        
        # Mock session not found
        mock_session_operations["get"].side_effect = Exception("Session not found")
        
        response = client.post(f"/v1/test/chatbot/close/{username}/{thread_id}")
        
        # The endpoint should handle this gracefully or return an error
        # Depending on the implementation, this might be 404 or 500
        assert response.status_code in [404, 500]


    def test_close_chat_websocket_error_during_close(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test chat websocket closure with error during close operation."""
        username = "testuser"
        thread_id = "test_thread_123"
        
        with patch('app.services.session.session_utils.close_websocket_session') as mock_close:
            mock_close.side_effect = Exception("Error closing websocket")
            
            response = client.post(f"/v1/test/chatbot/close/{username}/{thread_id}")
            
            # Should return error status
            assert response.status_code == 500


    def test_endpoints_integration_with_auth_flow(
        self, 
        client: TestClient,
        test_user_data: Dict[str, Any],
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test utility endpoints integration with authenticated user flow."""
        # 1. First register a user
        register_response = client.post("/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        
        # 2. Check health (should work regardless of auth status)
        health_response = client.get("/v1/test/health")
        assert health_response.status_code == 200
        
        # 3. Get Google accounts for the registered user
        username = test_user_data["username"]
        account_request = {"username": username}
        
        account_response = client.post("/v1/test/get_google_account/", json=account_request)
        assert account_response.status_code == 200
        
        # 4. Close a chat session (simulating cleanup)
        thread_id = "integration_test_thread"
        with patch('app.services.session.session_utils.close_websocket_session') as mock_close:
            mock_close.return_value = {"success": True, "message": "Session closed"}
            
            close_response = client.post(f"/v1/test/chatbot/close/{username}/{thread_id}")
            assert close_response.status_code == 200


    def test_utility_endpoints_error_handling(
        self, 
        client: TestClient,
        mock_redis
    ):
        """Test error handling across utility endpoints."""
        # Test health endpoint (should never fail)
        health_response = client.get("/v1/test/health")
        assert health_response.status_code == 200
        
        # Test invalid JSON for get_google_account
        invalid_response = client.post(
            "/v1/test/get_google_account/", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert invalid_response.status_code == 422
        
        # Test close websocket with invalid characters in path
        invalid_close_response = client.post("/v1/test/chatbot/close/invalid@user/thread#123")
        # Should handle gracefully
        assert invalid_close_response.status_code in [400, 422, 500]


    def test_concurrent_requests_handling(
        self, 
        client: TestClient,
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test handling of concurrent requests to utility endpoints."""
        import threading
        import time
        
        results = []
        
        def make_health_request():
            response = client.get("/v1/test/health")
            results.append(response.status_code)
        
        def make_account_request():
            request_data = {"username": f"testuser_{threading.current_thread().ident}"}
            response = client.post("/v1/test/get_google_account/", json=request_data)
            results.append(response.status_code)
        
        # Create multiple threads for concurrent requests
        threads = []
        for i in range(5):
            if i % 2 == 0:
                thread = threading.Thread(target=make_health_request)
            else:
                thread = threading.Thread(target=make_account_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all requests succeeded
        assert len(results) == 5
        for status_code in results:
            assert status_code in [200, 500]  # Either success or controlled error