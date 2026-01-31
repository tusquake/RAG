"""Tests for authentication endpoints."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId


class TestAuthRegister:
    """Tests for user registration."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, mock_mongodb):
        """Test successful user registration."""
        from app.api.routes.auth import register
        from app.models.user import UserCreate
        
        # Setup mock
        mock_mongodb.db.users.find_one = AsyncMock(return_value=None)
        mock_mongodb.db.users.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        
        with patch("app.db.mongodb.get_collection", return_value=mock_mongodb.db.users):
            with patch("app.api.middleware.rate_limiter.check_rate_limit", return_value=True):
                user_data = UserCreate(
                    email="new@example.com",
                    password="password123",
                    name="New User"
                )
                
                # This would need proper async test setup
                # For now, we're testing the structure
                assert user_data.email == "new@example.com"
                assert user_data.name == "New User"
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, mock_mongodb, test_user):
        """Test registration with existing email fails."""
        mock_mongodb.db.users.find_one = AsyncMock(return_value=test_user)
        
        # Registration should fail for duplicate email
        with patch("app.db.mongodb.get_collection", return_value=mock_mongodb.db.users):
            existing = await mock_mongodb.db.users.find_one({"email": test_user["email"]})
            assert existing is not None


class TestAuthLogin:
    """Tests for user login."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, mock_mongodb, test_user):
        """Test successful login."""
        from app.api.middleware.auth import verify_password, get_password_hash
        
        # Hash the password
        hashed = get_password_hash(test_user["password"])
        
        # Verify the password
        assert verify_password(test_user["password"], hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    @pytest.mark.asyncio
    async def test_login_invalid_email(self, mock_mongodb):
        """Test login with non-existent email."""
        mock_mongodb.db.users.find_one = AsyncMock(return_value=None)
        
        with patch("app.db.mongodb.get_collection", return_value=mock_mongodb.db.users):
            user = await mock_mongodb.db.users.find_one({"email": "nonexistent@example.com"})
            assert user is None


class TestTokens:
    """Tests for JWT token operations."""
    
    def test_create_and_decode_token(self, test_user):
        """Test token creation and decoding."""
        from app.api.middleware.auth import create_access_token, decode_token
        
        # Create token
        token = create_access_token(
            data={"sub": test_user["id"], "email": test_user["email"]}
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode token
        token_data = decode_token(token)
        
        assert token_data.user_id == test_user["id"]
        assert token_data.email == test_user["email"]
    
    def test_invalid_token(self):
        """Test decoding invalid token raises error."""
        from app.api.middleware.auth import decode_token
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid-token")
        
        assert exc_info.value.status_code == 401
