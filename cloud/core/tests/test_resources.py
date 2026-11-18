import pytest
from rest_framework.test import APIClient
from core.models import User, Tenant, TenantMembership, Home, HomeMembership, Room, Device


@pytest.fixture
def context(db):
    owner = User.objects.create_user(username="owner", email="owner@example.com", password="pass")
    resident = User.objects.create_user(username="resident", email="resident@example.com", password="pass")
    stranger = User.objects.create_user(username="stranger", email="stranger@example.com", password="pass")
    tenant = Tenant.objects.create(name="T")
    TenantMembership.objects.create(tenant=tenant, user=owner, role="owner")
    TenantMembership.objects.create(tenant=tenant, user=resident, role="member")
    home = Home.objects.create(tenant=tenant, name="H")
    HomeMembership.objects.create(home=home, user=owner, role="owner")
    HomeMembership.objects.create(home=home, user=resident, role="resident")
    other = Home.objects.create(tenant=Tenant.objects.create(name="Other"), name="Other")
    return owner, resident, stranger, home, other


def api(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_room_and_device_crud(context):
    owner, _, _, home, _ = context
    client = api(owner)
    room = client.post("/api/v1/rooms/", {"home": str(home.pk), "name": "Sala"}, format="json")
    assert room.status_code == 201, room.data
    device = client.post("/api/v1/devices/", {
        "home": str(home.pk), "room": room.data["id"], "name": "Luz",
        "kind": "light", "capabilities": ["on_off", "brightness"]
    }, format="json")
    assert device.status_code == 201, device.data
    assert device.data["state"] == {}
    assert device.data["is_available"] is False
    assert len(client.get(f"/api/v1/devices/?home={home.pk}").data) == 1
    assert client.patch(f"/api/v1/devices/{device.data['id']}/", {"name": "Luz sala"}, format="json").status_code == 200
    assert client.delete(f"/api/v1/devices/{device.data['id']}/").status_code == 204


@pytest.mark.django_db
def test_cross_home_room_rejected(context):
    owner, _, _, home, other = context
    room = Room.objects.create(home=other, name="Secret")
    response = api(owner).post("/api/v1/devices/", {
        "home": str(home.pk), "room": str(room.pk), "name": "Lamp"
    }, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_read_and_write_permissions(context):
    owner, resident, stranger, home, _ = context
    room = Room.objects.create(home=home, name="Sala")
    assert len(api(resident).get("/api/v1/rooms/").data) == 1
    assert api(resident).post("/api/v1/rooms/", {"home": str(home.pk), "name": "Quarto"}, format="json").status_code == 403
    assert api(resident).delete(f"/api/v1/rooms/{room.pk}/").status_code == 403
    assert api(stranger).get(f"/api/v1/rooms/{room.pk}/").status_code == 404
    assert api(stranger).get("/api/v1/rooms/").data == []
    assert APIClient().get("/api/v1/rooms/").status_code in (401, 403)


@pytest.mark.django_db
def test_cannot_write_device_state_from_cloud_api(context):
    owner, _, _, home, _ = context
    client = api(owner)
    response = client.post("/api/v1/devices/", {
        "home": str(home.pk), "name": "Lamp", "state": {"on": True}, "is_available": True
    }, format="json")
    assert response.status_code == 201
    assert response.data["state"] == {}
    assert response.data["is_available"] is False
    update = client.patch(f"/api/v1/devices/{response.data['id']}/", {"state": {"on": True}}, format="json")
    assert update.status_code == 200
    assert update.data["state"] == {}


@pytest.mark.django_db
def test_duplicate_room_name_rejected(context):
    owner, _, _, home, _ = context
    Room.objects.create(home=home, name="Sala")
    response = api(owner).post("/api/v1/rooms/", {"home": str(home.pk), "name": "Sala"}, format="json")
    assert response.status_code == 400
