"""
E2E tests for WebSocket endpoints.
Tests chat WebSocket connections, message handling, and session management.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import json
from typing import Dict, Any


class TestWebSocketEndpoints:
    """Test suite for WebSocket endpoints."""

    def test_websocket_connection_establishment(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket connection establishment."""
        username = "testuser"
        thread_id = "test_thread_123"
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            # Connection should be established successfully
            assert websocket is not None
            
            # Verify session initialization was called
            mock_session_operations["init"].assert_called_once()


    def test_websocket_message_echo(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket message echo functionality."""
        username = "testuser"
        thread_id = "test_thread_123"
        test_message = "Hello, this is a test message"
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            # Send a message
            websocket.send_text(test_message)
            
            # Receive response
            response = websocket.receive_text()
            
            # Should echo back with AI prefix and username
            assert f"AI : {test_message} - from {username}" == response


    def test_websocket_multiple_messages(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test handling multiple WebSocket messages."""
        username = "testuser"
        thread_id = "test_thread_123"
        messages = ["Message 1", "Message 2", "Message 3"]
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            for message in messages:
                websocket.send_text(message)
                response = websocket.receive_text()
                assert f"AI : {message} - from {username}" == response


    def test_websocket_connection_cleanup(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket connection cleanup."""
        username = "testuser"
        thread_id = "test_thread_123"
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            websocket.send_text("test message")
            websocket.receive_text()
        
        # After context manager exits, session cleanup should be called
        mock_session_operations["delete"].assert_called_once_with(
            username=username, 
            thread_id=thread_id
        )


    def test_websocket_invalid_username_characters(
        self, 
        client: TestClient,
        mock_redis
    ):
        """Test WebSocket with invalid username characters."""
        invalid_username = "user@invalid"
        thread_id = "test_thread_123"
        
        # Connection should still work as FastAPI handles path parameters
        with client.websocket_connect(f"/v1/chatbot/chatbot/{invalid_username}/{thread_id}") as websocket:
            websocket.send_text("test")
            response = websocket.receive_text()
            assert invalid_username in response


    def test_websocket_empty_message(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket with empty message."""
        username = "testuser"
        thread_id = "test_thread_123"
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            websocket.send_text("")
            response = websocket.receive_text()
            assert f"AI :  - from {username}" == response


    def test_websocket_long_message(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket with long message."""
        username = "testuser"
        thread_id = "test_thread_123"
        long_message = "A" * 1000  # 1000 character message
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            websocket.send_text(long_message)
            response = websocket.receive_text()
            assert long_message in response
            assert username in response


    def test_websocket_json_message(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket with JSON formatted message."""
        username = "testuser"
        thread_id = "test_thread_123"
        json_message = json.dumps({"type": "question", "content": "What is 2+2?"})
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            websocket.send_text(json_message)
            response = websocket.receive_text()
            assert json_message in response
            assert username in response


    def test_websocket_special_characters(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket with special characters in message."""
        username = "testuser"
        thread_id = "test_thread_123"
        special_message = "Hello! @#$%^&*()_+-={}[]|\\:;\"'<>,.?/~`"
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            websocket.send_text(special_message)
            response = websocket.receive_text()
            assert special_message in response


    def test_websocket_unicode_message(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket with Unicode characters."""
        username = "testuser"
        thread_id = "test_thread_123"
        unicode_message = "Hello 世界! 🌍 café naïve résumé"
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            websocket.send_text(unicode_message)
            response = websocket.receive_text()
            assert unicode_message in response


    def test_websocket_concurrent_connections(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test multiple concurrent WebSocket connections."""
        connections_data = [
            ("user1", "thread1", "Hello from user1"),
            ("user2", "thread2", "Hello from user2"),
            ("user3", "thread3", "Hello from user3"),
        ]
        
        # Create multiple websocket connections
        websockets = []
        for username, thread_id, _ in connections_data:
            ws = client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}")
            websockets.append((ws.__enter__(), username, thread_id))
        
        try:
            # Send messages from each connection
            for i, (websocket, username, thread_id) in enumerate(websockets):
                message = connections_data[i][2]
                websocket.send_text(message)
                response = websocket.receive_text()
                assert f"AI : {message} - from {username}" == response
        
        finally:
            # Clean up all connections
            for websocket, _, _ in websockets:
                websocket.__exit__(None, None, None)


    def test_websocket_session_initialization_error(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket behavior when session initialization fails."""
        username = "testuser"
        thread_id = "test_thread_123"
        
        # Mock session initialization failure
        mock_session_operations["init"].side_effect = Exception("Session init failed")
        
        # Connection should still be established, but behavior might be different
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            websocket.send_text("test message")
            # Depending on implementation, this might still echo or handle the error
            response = websocket.receive_text()
            # Should receive some response (either echo or error message)
            assert response is not None


    @pytest.mark.asyncio
    async def test_websocket_connection_persistence(
        self, 
        client: TestClient,
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket connection persistence over time."""
        username = "testuser"
        thread_id = "test_thread_123"
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            # Send initial message
            websocket.send_text("Initial message")
            initial_response = websocket.receive_text()
            assert "Initial message" in initial_response
            
            # Wait briefly to simulate time passage
            await asyncio.sleep(0.1)
            
            # Send another message to ensure connection is still active
            websocket.send_text("Follow-up message")
            follow_up_response = websocket.receive_text()
            assert "Follow-up message" in follow_up_response


    def test_websocket_integration_with_auth(
        self, 
        client: TestClient,
        test_user_data: Dict[str, Any],
        mock_database_operations: Dict[str, Any],
        mock_session_operations: Dict[str, Any],
        mock_redis
    ):
        """Test WebSocket integration after user authentication."""
        # 1. Register user first
        register_response = client.post("/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        
        # 2. Use registered username for WebSocket connection
        username = test_user_data["username"]
        thread_id = "auth_integration_thread"
        
        with client.websocket_connect(f"/v1/chatbot/chatbot/{username}/{thread_id}") as websocket:
            websocket.send_text("Hello from authenticated user")
            response = websocket.receive_text()
            assert username in response
            assert "Hello from authenticated user" in response