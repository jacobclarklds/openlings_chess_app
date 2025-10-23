"""
Tests for OAuth authentication flow
Note: These tests mock OAuth responses since we can't test real OAuth flow in unit tests
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import status


class TestGoogleOAuth:
    """Test Google OAuth integration"""

    @pytest.mark.asyncio
    async def test_google_login_redirect(self, client):
        """Test that Google login initiates OAuth flow"""
        # Mock the OAuth redirect
        with patch('app.api.auth.oauth.google.authorize_redirect') as mock_redirect:
            mock_redirect.return_value = MagicMock(status_code=302)

            response = client.get("/api/auth/google/login")

            # The endpoint should attempt to redirect
            assert mock_redirect.called

    @pytest.mark.asyncio
    async def test_google_callback_new_user(self, client, db_session):
        """Test Google callback creates new user"""
        mock_token = {
            'userinfo': {
                'email': 'newgoogleuser@gmail.com',
                'sub': 'google_sub_123',
                'name': 'Test User',
                'picture': 'https://example.com/pic.jpg'
            }
        }

        with patch('app.api.auth.oauth.google.authorize_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_token

            # Mock the request object
            from starlette.requests import Request
            mock_request = MagicMock(spec=Request)

            # We can't easily test the full redirect, but we can test the logic
            # by directly calling the endpoint function
            from app.api.auth import google_callback
            from app.core.database import get_db

            # Override get_db to use test session
            def override_get_db():
                yield db_session

            response = await google_callback(mock_request, db_session)

            # Should redirect to frontend with token
            assert response.status_code == 307  # Redirect
            assert 'token=' in response.headers.get('location', '')

    @pytest.mark.asyncio
    async def test_google_callback_existing_user(self, client, test_user, db_session):
        """Test Google callback with existing user email"""
        mock_token = {
            'userinfo': {
                'email': test_user.email,
                'sub': 'google_sub_456',
                'name': 'Test User',
                'picture': 'https://example.com/pic.jpg'
            }
        }

        with patch('app.api.auth.oauth.google.authorize_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_token

            from starlette.requests import Request
            mock_request = MagicMock(spec=Request)

            from app.api.auth import google_callback

            response = await google_callback(mock_request, db_session)

            # Should successfully link OAuth to existing account
            assert response.status_code == 307

            # Verify user was updated with OAuth info
            db_session.refresh(test_user)
            assert test_user.oauth_provider == 'google'
            assert test_user.oauth_provider_id == 'google_sub_456'

    @pytest.mark.asyncio
    async def test_google_callback_no_email(self, client, db_session):
        """Test Google callback fails without email"""
        mock_token = {
            'userinfo': {
                'sub': 'google_sub_789',
                'name': 'Test User',
                # Missing email
            }
        }

        with patch('app.api.auth.oauth.google.authorize_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_token

            from starlette.requests import Request
            mock_request = MagicMock(spec=Request)

            from app.api.auth import google_callback

            # Should raise HTTPException
            with pytest.raises(Exception):  # Will be HTTPException
                await google_callback(mock_request, db_session)

    @pytest.mark.asyncio
    async def test_google_callback_no_userinfo(self, client, db_session):
        """Test Google callback fails without userinfo"""
        mock_token = {
            # Missing userinfo
            'access_token': 'some_token'
        }

        with patch('app.api.auth.oauth.google.authorize_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_token

            from starlette.requests import Request
            mock_request = MagicMock(spec=Request)

            from app.api.auth import google_callback

            # Should raise HTTPException
            with pytest.raises(Exception):
                await google_callback(mock_request, db_session)


class TestOAuthUserCreation:
    """Test OAuth user creation logic"""

    def test_oauth_user_has_no_password(self, test_oauth_user):
        """Test that OAuth users don't have passwords"""
        assert test_oauth_user.hashed_password is None
        assert test_oauth_user.oauth_provider == 'google'
        assert test_oauth_user.oauth_provider_id is not None

    def test_oauth_user_has_profile_picture(self, test_oauth_user):
        """Test that OAuth users get profile picture"""
        assert test_oauth_user.profile_picture is not None
        assert test_oauth_user.profile_picture.startswith('http')

    def test_regular_user_no_oauth_fields(self, test_user):
        """Test that regular users don't have OAuth fields"""
        assert test_user.oauth_provider is None
        assert test_user.oauth_provider_id is None
        assert test_user.hashed_password is not None


class TestOAuthSecurity:
    """Test OAuth security measures"""

    def test_oauth_user_cannot_login_with_password(self, client, test_oauth_user):
        """Test OAuth users must use OAuth to login"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_oauth_user.email,
                "password": "anypassword",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        detail = response.json()["detail"]
        assert "google" in detail.lower()
        assert "sign in with" in detail.lower()

    def test_oauth_token_creates_valid_jwt(self, client, test_oauth_user):
        """Test that OAuth users get valid JWT tokens"""
        from app.core.security import create_access_token

        # Simulate what happens in OAuth callback
        token = create_access_token(data={"sub": test_oauth_user.email})

        # Token should work for authentication
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == test_oauth_user.email


class TestOAuthEdgeCases:
    """Test edge cases in OAuth flow"""

    @pytest.mark.asyncio
    async def test_oauth_username_generation(self, client, db_session):
        """Test that OAuth generates unique usernames"""
        mock_token = {
            'userinfo': {
                'email': 'test@gmail.com',
                'sub': 'abc123',
                'name': 'Test User',
                'picture': 'https://example.com/pic.jpg'
            }
        }

        with patch('app.api.auth.oauth.google.authorize_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_token

            from starlette.requests import Request
            from app.api.auth import google_callback
            from app.models.user import User

            mock_request = MagicMock(spec=Request)

            await google_callback(mock_request, db_session)

            # Check that user was created with generated username
            user = db_session.query(User).filter(User.email == 'test@gmail.com').first()
            assert user is not None
            assert user.username.startswith('test_')
            assert 'abc123' in user.username

    def test_oauth_user_profile_in_response(self, client, test_oauth_user):
        """Test that OAuth profile info is included in user response"""
        from app.core.security import create_access_token

        token = create_access_token(data={"sub": test_oauth_user.email})

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        data = response.json()
        assert "oauth_provider" in data
        assert "oauth_provider_id" in data
        assert "profile_picture" in data
        assert data["oauth_provider"] == "google"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
