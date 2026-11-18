import pytest
from rest_framework.test import APIClient
from core.models import User


@pytest.mark.django_db
def test_login_and_authenticated_request():
    user = User.objects.create_user(
        username="alice", email="alice@example.com", password="strong-password-123"
    )
    client = APIClient()
    response = client.post(
        "/api/v1/auth/login/",
        {"username": "alice", "password": "strong-password-123"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["access"]
    assert response.data["refresh"]

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    assert client.get("/api/v1/tenants/").status_code == 200

    refresh = client.post(
        "/api/v1/auth/refresh/",
        {"refresh": response.data["refresh"]},
        format="json",
    )
    assert refresh.status_code == 200
    assert refresh.data["access"]


@pytest.mark.django_db
def test_login_rejects_wrong_password():
    User.objects.create_user(
        username="alice", email="alice@example.com", password="strong-password-123"
    )
    response = APIClient().post(
        "/api/v1/auth/login/",
        {"username": "alice", "password": "wrong"},
        format="json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_rejects_inactive_user():
    User.objects.create_user(
        username="alice", email="alice@example.com",
        password="strong-password-123", is_active=False
    )
    response = APIClient().post(
        "/api/v1/auth/login/",
        {"username": "alice", "password": "strong-password-123"},
        format="json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_invalid_token_is_rejected():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
    assert client.get("/api/v1/tenants/").status_code == 401
