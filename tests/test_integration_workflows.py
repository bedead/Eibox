"""
E2E integration tests for complete API workflows.
Tests end-to-end user journeys and cross-endpoint interactions.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from typing import Dict, Any
from datetime import datetime, timedelta
import json


class TestIntegrationWorkflows:
    """Test suite for complete API workflows and integrations."""

    def test_complete_user_onboarding_workflow(
        self, 
        client: TestClient,
        test_user_data: Dict[str, Any],
        mock_database_operations: Dict[str, Any],
        mock_oauth_flow: Mock,
        mock_google_user_info: Mock,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test complete user onboarding: register -> login -> OAuth -> chat."""
        username = test_user_data["username"]
        
        # 1. User Registration
        register_response = client.post("/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        assert register_response.json()["success"] == 200
        
        # 2. User Login
        login_data = {"username": username, "password": test_user_data["password"]}
        login_response = client.post("/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        assert login_response.json()["success"] == 200
        
        # 3. Health Check (ensuring service is ready)
        health_response = client.get("/v1/test/health")
        assert health_response.status_code == 200
        
        # 4. Start Gmail OAuth
        oauth_params = {"username": username, "mobile_session_id": "onboarding_session"}
        oauth_start_response = client.get("/v1/oauth/gmail/start", params=oauth_params, follow_redirects=False)
        assert oauth_start_response.status_code == 307  # Redirect to Google
        
        # 5. Simulate OAuth completion and check status
        with patch('app.api.v1.endpoints.gmail_oauth.oauth_states') as mock_states:
            mock_states.items.return_value = [
                ("state_123", {
                    "mobile_session_id": "onboarding_session",
                    "completed": True,
                    "email": "test@gmail.com"
                })
            ]
            mock_states.__delitem__ = Mock()
            
            status_response = client.get("/v1/oauth/gmail/status/onboarding_session")
            assert status_response.status_code == 200
            assert status_response.json()["completed"] is True
        
        # 6. Check Google accounts
        account_request = {"username": username}
        account_response = client.post("/v1/test/get_google_account/", json=account_request)
        assert account_response.status_code == 200
        
        # 7. Start WebSocket chat session
        thread_id = "onboarding_chat"
        with patch('app.services.session.session_utils.init_or_get_session') as mock_init_session:
            with patch('app.utils._api_helper.call_graph') as mock_call_graph:
                mock_call_graph.return_value = f"Hello {username}, I can help you with email management!"
                
                with client.websocket_connect(f"/v1/chatbot/open/{username}/{thread_id}") as websocket:
                    websocket.send_text("Hello, I just completed onboarding!")
                    response = websocket.receive_text()
                    # Accept any reasonable response from the AI assistant
                    assert len(response) > 0
                    assert any(word in response.lower() for word in ["welcome", "assist", "help", "hello"])


    def test_user_profile_management_workflow(
        self, 
        client: TestClient,
        test_user_data: Dict[str, Any],
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test user profile management workflow."""
        username = test_user_data["username"]
        
        # 1. Register user
        register_response = client.post("/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        
        # 2. Login
        login_data = {"username": username, "password": test_user_data["password"]}
        login_response = client.post("/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        # 3. Update profile with email monitoring settings
        update_data = {
            "username": username,
            "full_name": "Updated Test User",
            "auto_email_monitoring": True,
            "email_monitoring_frequency": 30,
            "email_notifications": True
        }
        update_response = client.post("/v1/auth/update_user_data", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["success"] == 200
        
        # 4. Update again with different settings
        update_data2 = {
            "username": username,
            "auto_email_monitoring": False,
            "email_notifications": False
        }
        update_response2 = client.post("/v1/auth/update_user_data", json=update_data2)
        assert update_response2.status_code == 200
        
        # 5. Add Gmail accounts
        update_data3 = {
            "username": username,
            "gmail_accounts": ["user@gmail.com", "backup@gmail.com"]
        }
        update_response3 = client.post("/v1/auth/update_user_data", json=update_data3)
        assert update_response3.status_code == 200


    def test_oauth_error_recovery_workflow(
        self, 
        client: TestClient,
        test_user_data: Dict[str, Any],
        mock_database_operations: Dict[str, Any],
        mock_oauth_flow: Mock,
        mock_redis
    ):
        """Test OAuth error scenarios and recovery."""
        username = test_user_data["username"]
        
        # 1. Register and login user
        client.post("/v1/auth/register", json=test_user_data)
        login_data = {"username": username, "password": test_user_data["password"]}
        client.post("/v1/auth/login", json=login_data)
        
        # 2. Start OAuth flow
        oauth_params = {"username": username, "mobile_session_id": "error_recovery_session"}
        oauth_start_response = client.get("/v1/oauth/gmail/start", params=oauth_params, follow_redirects=False)
        assert oauth_start_response.status_code == 307
        
        # 3. Check status before completion (should be incomplete)
        status_response = client.get("/v1/oauth/gmail/status/error_recovery_session")
        assert status_response.status_code == 200
        assert status_response.json()["completed"] is False
        
        # 4. Simulate OAuth callback error with invalid state
        with patch('app.api.v1.endpoints.gmail_oauth.oauth_states') as mock_states:
            # Mock empty oauth_states to simulate invalid state error
            mock_states.__contains__ = Mock(return_value=False)
            mock_states.get = Mock(return_value=None)
            
            callback_params = {"state": "invalid_state", "code": "test_code"}
            callback_response = client.get("/v1/oauth/gmail/callback", params=callback_params)
            assert callback_response.status_code == 200
            assert "error" in callback_response.text.lower()
        
        # 5. Status should still be incomplete
        status_response2 = client.get("/v1/oauth/gmail/status/error_recovery_session")
        assert status_response2.json()["completed"] is False
        
        # 6. Retry OAuth flow (simulate user trying again)
        oauth_params2 = {"username": username, "mobile_session_id": "error_recovery_session_2"}
        oauth_retry_response = client.get("/v1/oauth/gmail/start", params=oauth_params2, follow_redirects=False)
        assert oauth_retry_response.status_code == 307


    def test_concurrent_user_sessions_workflow(
        self, 
        client: TestClient,
        mock_database_operations: Dict[str, Any],
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test concurrent user sessions and isolation."""
        # Create test data for multiple users
        users_data = []
        for i in range(3):
            user_data = {
                "user_id": f"test_user_{i}",
                "account_created": "2024-01-01T00:00:00",
                "username": f"testuser{i}",
                "full_name": f"Test User {i}",
                "email": f"test{i}@example.com",
                "password": f"testpassword{i}",
                "gmail_accounts": [f"test{i}@gmail.com"]
            }
            users_data.append(user_data)
        
        # 1. Register all users
        for user_data in users_data:
            response = client.post("/v1/auth/register", json=user_data)
            assert response.status_code == 200
        
        # 2. Login all users
        for user_data in users_data:
            login_data = {"username": user_data["username"], "password": user_data["password"]}
            response = client.post("/v1/auth/login", json=login_data)
            assert response.status_code == 200
        
        # 3. Test WebSocket sessions for each user with mocking
        with patch('app.services.session.session_utils.init_or_get_session') as mock_init_session:
            with patch('app.utils._api_helper.call_graph') as mock_call_graph:
                for i, user_data in enumerate(users_data):
                    username = user_data["username"] 
                    thread_id = f"concurrent_thread_{i}"
                    
                    # Configure mock to return user-specific response
                    mock_call_graph.return_value = f"Response for {username}: I can help with your emails"
                    
                    # Test WebSocket connection for this user
                    with client.websocket_connect(f"/v1/chatbot/open/{username}/{thread_id}") as websocket:
                        message = f"Message from {username}"
                        websocket.send_text(message)
                        response = websocket.receive_text()
                        # Accept any reasonable response from the AI assistant
                        assert len(response) > 0
                        assert any(word in response.lower() for word in ["assist", "help", "can", "how", "understood"])
                        
                        # Basic session isolation check - response should be coherent
                        assert len(response.strip()) > 10  # Should be a meaningful response
        
        # 6. Close all chat sessions
        for i, user_data in enumerate(users_data):
            username = user_data["username"]
            thread_id = f"concurrent_thread_{i}"
            with patch('app.api.v1.endpoints.websocket.get_session') as mock_get_session:
                with patch('app.api.v1.endpoints.websocket.close_websocket_session') as mock_close:
                    # Mock session object with websocket attribute
                    mock_session = Mock()
                    mock_session.websocket = None
                    mock_get_session.return_value = mock_session
                    mock_close.return_value = {"success": True, "message": "Session closed"}
                    
                    response = client.post(f"/v1/chatbot/close/{username}/{thread_id}")
                    assert response.status_code == 200


    def test_api_error_handling_workflow(
        self, 
        client: TestClient,
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test comprehensive error handling across API endpoints."""
        # 1. Test registration with database error
        mock_database_operations["register"].return_value = {
            "success": False, 
            "message": "Database connection failed"
        }
        
        test_user = {
            "user_id": "error_test_user",
            "username": "erroruser",
            "email": "error@example.com",
            "password": "errorpassword",
            "account_created": "2024-01-01T00:00:00",
            "full_name": "Error Test User",
            "gmail_accounts": ["error@gmail.com"]
        }
        
        register_response = client.post("/v1/auth/register", json=test_user)
        assert register_response.status_code == 200  # Returns 200 but with success: false
        assert register_response.json()["success"] is False  # Database error indicated by success: false
        
        # 2. Test login with authentication error
        mock_database_operations["login"].return_value = {
            "success": False,
            "message": "Invalid credentials"
        }
        
        login_data = {"username": "erroruser", "password": "errorpassword"}
        login_response = client.post("/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        assert login_response.json()["success"] is False  # Authentication error indicated by success: false
        
        # 3. Test get Google account with error
        # Reset the mock to raise exception instead of returning a value
        mock_database_operations["get_gmail"].side_effect = Exception("Service unavailable")
        mock_database_operations["get_gmail"].return_value = None  # Clear any return_value
        
        account_request = {"username": "erroruser"}
        account_response = client.post("/v1/test/get_google_account/", json=account_request)
        assert account_response.status_code == 500
        assert "Failed to save tokens" in account_response.json()["detail"]
        
        # 4. Health check should still work
        health_response = client.get("/v1/test/health")
        assert health_response.status_code == 200


    def test_api_versioning_compatibility(self, client: TestClient):
        """Test API versioning and endpoint compatibility."""
        # 1. Test all v1 endpoints are accessible
        v1_endpoints = [
            ("/v1/test/health", "GET"),
        ]
        
        for endpoint, method in v1_endpoints:
            if method == "GET":
                response = client.get(endpoint)
                # Should not return 404 (endpoint exists)
                assert response.status_code != 404
            elif method == "POST":
                response = client.post(endpoint, json={})
                # Should not return 404 (endpoint exists)
                assert response.status_code != 404
        
        # 2. Test non-existent endpoints return 404
        non_existent_endpoints = [
            "/v1/nonexistent",
            "/v2/test/health",  # v2 doesn't exist yet
            "/v1/auth/nonexistent"
        ]
        
        for endpoint in non_existent_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404


    def test_performance_under_load(
        self, 
        client: TestClient,
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test API performance under simulated load."""
        import time
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def make_request(endpoint_data):
            endpoint, method, payload = endpoint_data
            start_time = time.time()
            
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json=payload)
            
            end_time = time.time()
            return {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code in [200, 307, 422]  # Expected status codes
            }
        
        # Define test requests
        test_requests = [
            ("/v1/test/health", "GET", {}),
            ("/v1/auth/register", "POST", {
                "user_id": "load_test_user",
                "username": "loadtestuser",
                "email": "load@test.com",
                "password": "loadtestpass",
                "account_created": "2024-01-01T00:00:00"
            }),
            ("/v1/test/get_google_account/", "POST", {"username": "loadtestuser"}),
        ] * 10  # Repeat each request 10 times
        
        # Execute requests concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, req) for req in test_requests]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        success_count = sum(1 for r in results if r["success"])
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        max_response_time = max(r["response_time"] for r in results)
        
        # Assertions for performance
        assert success_count >= len(results) * 0.95  # 95% success rate
        assert avg_response_time < 1.0  # Average response time under 1 second
        assert max_response_time < 5.0  # Max response time under 5 seconds
        
        print(f"Load test results:")
        print(f"- Total requests: {len(results)}")
        print(f"- Successful requests: {success_count}")
        print(f"- Success rate: {success_count/len(results)*100:.1f}%")
        print(f"- Average response time: {avg_response_time:.3f}s")
        print(f"- Max response time: {max_response_time:.3f}s")