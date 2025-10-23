"""
Tests for authentication endpoints
"""
import pytest
from fastapi import status


class TestRegistration:
    """Test user registration"""

    def test_register_new_user(self, client):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "hashed_password" not in data
        assert "id" in data
        assert data["is_active"] is True

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email fails"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "username": "differentuser",
                "password": "password123",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with existing username fails"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user.username,
                "password": "password123",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_register_weak_password(self, client):
        """Test registration with weak password fails"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": "12345",  # Less than 6 characters
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "6 characters" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """Test registration with invalid email fails"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "password123",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Test user login"""

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,  # OAuth2 uses 'username' field
                "password": "password123",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user fails"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_oauth_user_with_password(self, client, test_oauth_user):
        """Test that OAuth users cannot login with password"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_oauth_user.email,
                "password": "anypassword",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "google" in response.json()["detail"].lower()


class TestCurrentUser:
    """Test getting current user info"""

    def test_get_current_user(self, client, test_user, auth_headers):
        """Test getting current user info with valid token"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["id"] == test_user.id

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token fails"""
        response = client.get("/api/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token fails"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_oauth_fields(self, client, test_oauth_user, db_session):
        """Test that OAuth user fields are returned"""
        # Login as OAuth user (create token manually)
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": test_oauth_user.email})

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["oauth_provider"] == "google"
        assert data["oauth_provider_id"] == "google_12345"
        assert data["profile_picture"] == "https://example.com/pic.jpg"


class TestTokenValidation:
    """Test JWT token validation"""

    def test_expired_token(self, client, test_user):
        """Test that expired tokens are rejected"""
        from datetime import timedelta
        from app.core.security import create_access_token

        # Create token that expires immediately
        token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(seconds=-1),
        )

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_with_missing_email(self, client):
        """Test that tokens without email are rejected"""
        from app.core.security import create_access_token

        # Create token without email in 'sub'
        token = create_access_token(data={"user_id": 123})

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_for_deleted_user(self, client, test_user, db_session):
        """Test that tokens for deleted users are rejected"""
        from app.core.security import create_access_token

        # Create valid token
        token = create_access_token(data={"sub": test_user.email})

        # Delete user
        db_session.delete(test_user)
        db_session.commit()

        # Token should now be invalid
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
