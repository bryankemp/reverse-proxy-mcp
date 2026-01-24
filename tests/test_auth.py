"""Unit tests for authentication endpoints."""

import pytest
from fastapi import status

from nginx_manager.models.database import User


@pytest.mark.unit
class TestAuthentication:
    """Test authentication endpoints."""

    def test_login_success(self, client, admin_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123456"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_invalid_username(self, client):
        """Test login with invalid username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_password(self, client, admin_user):
        """Test login with invalid password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, client, db):
        """Test login with inactive user."""
        from nginx_manager.core.security import hash_password
        from nginx_manager.models.database import User

        user = User(
            username="inactive",
            email="inactive@test.com",
            password_hash=hash_password("password123"),
            role="user",
            is_active=False,
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "inactive", "password": "password123"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_logout(self, client, auth_headers):
        """Test logout endpoint."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "detail" in data


@pytest.mark.unit
class TestUserManagement:
    """Test user management endpoints."""

    def test_list_users_admin(self, client, auth_headers, admin_user, regular_user):
        """Test listing users as admin."""
        response = client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert len(users) >= 2
        usernames = [u["username"] for u in users]
        assert "admin" in usernames
        assert "user" in usernames

    def test_list_users_unauthorized(self, client, user_auth_headers):
        """Test listing users as regular user."""
        response = client.get("/api/v1/users", headers=user_auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_self(self, client, user_auth_headers, regular_user):
        """Test getting own user profile."""
        response = client.get(f"/api/v1/users/{regular_user.id}", headers=user_auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "user"
        assert data["role"] == "user"

    def test_get_user_other_forbidden(self, client, user_auth_headers, admin_user):
        """Test getting other user profile as regular user."""
        response = client.get(f"/api/v1/users/{admin_user.id}", headers=user_auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_user_admin(self, client, auth_headers):
        """Test creating user as admin."""
        response = client.post(
            "/api/v1/users",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "newpass123456",
                "role": "user",
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "user"

    def test_create_user_duplicate_username(self, client, auth_headers, admin_user):
        """Test creating user with duplicate username."""
        response = client.post(
            "/api/v1/users",
            json={
                "username": "admin",
                "email": "duplicate@test.com",
                "password": "pass123456",
                "role": "user",
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_user_unauthorized(self, client, user_auth_headers):
        """Test creating user as regular user."""
        response = client.post(
            "/api/v1/users",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "pass123456",
                "role": "user",
            },
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_email(self, client, auth_headers, regular_user):
        """Test updating user email."""
        response = client.put(
            f"/api/v1/users/{regular_user.id}",
            json={"email": "newemail@test.com"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newemail@test.com"

    def test_delete_user_admin(self, client, auth_headers, db, regular_user):
        """Test deleting user as admin."""
        user_id = regular_user.id
        response = client.delete(
            f"/api/v1/users/{user_id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify soft delete (user still exists but is_active=False)
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            assert user.is_active is False

    def test_change_password_own(self, client, user_auth_headers, regular_user):
        """Test changing own password."""
        response = client.post(
            f"/api/v1/users/{regular_user.id}/change-password",
            json={
                "old_password": "user123456",
                "new_password": "newpass123456",
            },
            params={
                "user_id": regular_user.id,
                "old_password": "user123456",
                "new_password": "newpass123456",
            },
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_invalid_old(self, client, user_auth_headers, regular_user):
        """Test changing password with wrong old password."""
        response = client.post(
            f"/api/v1/users/{regular_user.id}/change-password",
            params={
                "user_id": regular_user.id,
                "old_password": "wrongpass",
                "new_password": "newpass123456",
            },
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
