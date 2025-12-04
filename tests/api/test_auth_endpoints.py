"""
E2E tests for authentication endpoints.
Tests user registration, login, and user data updates.
"""
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any


class TestAuthEndpoints:
    """Test suite for authentication endpoints."""

    def test_user_registration_success(
        self, 
        client: TestClient, 
        test_user_data: Dict[str, Any], 
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test successful user registration."""
        response = client.post("/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == 200
        assert "User registered successfully" in response_data["message"]
        
        # Verify the database operation was called
        mock_database_operations["register"].assert_called_once()


    def test_user_registration_validation_error(self, client: TestClient):
        """Test user registration with invalid data."""
        invalid_data = {
            "user_id": "",  # Empty user_id should cause validation error
            "username": "testuser",
            "email": "invalid-email",  # Invalid email format
            "password": ""  # Empty password
        }
        
        response = client.post("/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error


    def test_user_registration_missing_required_fields(self, client: TestClient):
        """Test user registration with missing required fields."""
        incomplete_data = {
            "username": "testuser"
            # Missing required fields: user_id, email, password, etc.
        }
        
        response = client.post("/v1/auth/register", json=incomplete_data)
        assert response.status_code == 422


    def test_user_login_success(
        self, 
        client: TestClient, 
        test_login_data: Dict[str, str], 
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test successful user login."""
        response = client.post("/v1/auth/login", json=test_login_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == 200
        assert "User logged in successfully" in response_data["message"]
        assert "data" in response_data
        
        # Verify the database operation was called
        mock_database_operations["login"].assert_called_once()


    def test_user_login_invalid_credentials(
        self, 
        client: TestClient, 
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test login with invalid credentials."""
        # Mock failed login - should raise HTTPException
        from fastapi import HTTPException
        mock_database_operations["login"].side_effect = HTTPException(status_code=401, detail="Invalid credentials")
        
        invalid_login = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = client.post("/v1/auth/login", json=invalid_login)
        
        assert response.status_code == 401  # Should return HTTP 401 for invalid credentials
        response_data = response.json()
        assert "Invalid credentials" in response_data["detail"]


    def test_user_login_missing_fields(self, client: TestClient):
        """Test login with missing required fields."""
        incomplete_login = {"username": "testuser"}  # Missing password
        
        response = client.post("/v1/auth/login", json=incomplete_login)
        assert response.status_code == 422


    def test_update_user_data_success(
        self, 
        client: TestClient, 
        test_update_data: Dict[str, Any], 
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test successful user data update."""
        response = client.post("/v1/auth/update_user_data", json=test_update_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == 200
        assert "User details updated successfully" in response_data["message"]
        
        # Verify the database operation was called
        mock_database_operations["update"].assert_called_once()


    def test_update_user_data_partial_update(
        self, 
        client: TestClient, 
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test partial user data update."""
        partial_update = {
            "username": "testuser",
            "auto_email_monitoring": True,  # Only updating this field
        }
        
        response = client.post("/v1/auth/update_user_data", json=partial_update)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == 200
        
        # Verify the database operation was called
        mock_database_operations["update"].assert_called_once()


    def test_update_user_data_missing_username(self, client: TestClient):
        """Test user data update without username."""
        update_without_username = {
            "full_name": "Test User",
            "auto_email_monitoring": True
        }
        
        response = client.post("/v1/auth/update_user_data", json=update_without_username)
        assert response.status_code == 422  # Username is required


    def test_update_user_data_database_error(
        self, 
        client: TestClient, 
        test_update_data: Dict[str, Any], 
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test user data update with database error."""
        # Mock database error - should raise HTTPException
        from fastapi import HTTPException
        mock_database_operations["update"].side_effect = HTTPException(status_code=500, detail="Database connection error")
        
        response = client.post("/v1/auth/update_user_data", json=test_update_data)
        
        assert response.status_code == 500  # Should return HTTP 500 for database error
        response_data = response.json()
        assert "Database connection error" in response_data["detail"]


    def test_auth_endpoints_integration_flow(
        self, 
        client: TestClient, 
        test_user_data: Dict[str, Any],
        test_login_data: Dict[str, str], 
        test_update_data: Dict[str, Any],
        mock_database_operations: Dict[str, Any],
        mock_redis
    ):
        """Test complete auth flow: register -> login -> update."""
        # 1. Register user
        register_response = client.post("/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        assert register_response.json()["success"] == 200
        
        # 2. Login with registered user
        login_response = client.post("/v1/auth/login", json=test_login_data)
        assert login_response.status_code == 200
        assert login_response.json()["success"] == 200
        
        # 3. Update user data
        update_response = client.post("/v1/auth/update_user_data", json=test_update_data)
        assert update_response.status_code == 200
        assert update_response.json()["success"] == 200
        
        # Verify all database operations were called
        mock_database_operations["register"].assert_called_once()
        mock_database_operations["login"].assert_called_once()
        mock_database_operations["update"].assert_called_once()