import pytest
from rest_framework.test import APIClient

from core.models import Home, HomeMembership, Tenant, TenantMembership, User


@pytest.fixture
def users(db):
    return [
        User.objects.create_user(username=name, email=f"{name}@example.com", password="pass-123456")
        for name in ("alice", "bob", "charlie")
    ]


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_requires_authentication():
    assert APIClient().get("/api/v1/tenants/").status_code in (401, 403)


@pytest.mark.django_db
def test_tenant_creation_assigns_owner(users):
    alice = users[0]
    response = client_for(alice).post("/api/v1/tenants/", {"name": "Company"}, format="json")
    assert response.status_code == 201
    assert TenantMembership.objects.filter(
        tenant_id=response.data["id"], user=alice, role="owner"
    ).exists()


@pytest.mark.django_db
def test_tenant_isolation(users):
    alice, bob, _ = users
    tenant = Tenant.objects.create(name="Alice only")
    TenantMembership.objects.create(tenant=tenant, user=alice, role="owner")
    assert len(client_for(bob).get("/api/v1/tenants/").data) == 0
    assert client_for(bob).get(f"/api/v1/tenants/{tenant.pk}/").status_code == 404


@pytest.mark.django_db
def test_home_creation_requires_tenant_admin(users):
    alice, bob, _ = users
    tenant = Tenant.objects.create(name="Tenant")
    TenantMembership.objects.create(tenant=tenant, user=alice, role="owner")
    TenantMembership.objects.create(tenant=tenant, user=bob, role="member")
    payload = {"tenant": str(tenant.pk), "name": "Living room"}
    assert client_for(bob).post("/api/v1/homes/", payload, format="json").status_code == 403
    result = client_for(alice).post("/api/v1/homes/", payload, format="json")
    assert result.status_code == 201
    assert HomeMembership.objects.filter(home_id=result.data["id"], user=alice, role="owner").exists()


@pytest.mark.django_db
def test_home_isolation_and_membership(users):
    alice, bob, charlie = users
    tenant = Tenant.objects.create(name="Tenant")
    TenantMembership.objects.create(tenant=tenant, user=alice, role="owner")
    TenantMembership.objects.create(tenant=tenant, user=bob, role="member")
    home = Home.objects.create(tenant=tenant, name="Private home")
    assert client_for(bob).get(f"/api/v1/homes/{home.pk}/").status_code == 404
    assert client_for(charlie).get(f"/api/v1/homes/{home.pk}/").status_code == 404
    HomeMembership.objects.create(home=home, user=bob, role="resident")
    assert client_for(bob).get(f"/api/v1/homes/{home.pk}/").status_code == 200


@pytest.mark.django_db
def test_cannot_add_user_from_other_tenant_to_home(users):
    alice, bob, _ = users
    tenant = Tenant.objects.create(name="Tenant")
    TenantMembership.objects.create(tenant=tenant, user=alice, role="owner")
    home = Home.objects.create(tenant=tenant, name="Home")
    response = client_for(alice).post(
        f"/api/v1/homes/{home.pk}/members/",
        {"user": str(bob.pk), "role": "guest"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_non_admin_cannot_invite_tenant_members(users):
    alice, bob, charlie = users
    tenant = Tenant.objects.create(name="Tenant")
    TenantMembership.objects.create(tenant=tenant, user=alice, role="owner")
    TenantMembership.objects.create(tenant=tenant, user=bob, role="member")
    response = client_for(bob).post(
        f"/api/v1/tenants/{tenant.pk}/members/",
        {"user": str(charlie.pk), "role": "admin"}, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_cannot_assign_owner_role_from_membership_api(users):
    alice, bob, _ = users
    tenant = Tenant.objects.create(name="Tenant")
    TenantMembership.objects.create(tenant=tenant, user=alice, role="owner")
    response = client_for(alice).post(
        f"/api/v1/tenants/{tenant.pk}/members/",
        {"user": str(bob.pk), "role": "owner"}, format="json"
    )
    assert response.status_code == 400
