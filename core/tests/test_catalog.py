import io
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from core.models import Device, DeviceModel, DeviceType, Home, Tenant, User


def client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.mark.django_db
def test_catalog_is_shared_but_staff_writes_only():
    staff = User.objects.create_user(username="staff", email="staff@example.com", password="p", is_staff=True)
    regular = User.objects.create_user(username="regular", email="regular@example.com", password="p")
    assert client(regular).post("/api/v1/device-types/", {"slug": "outlet", "name": "Tomada"}, format="json").status_code == 403
    result = client(staff).post("/api/v1/device-types/", {"slug": "outlet", "name": "Tomada"}, format="json")
    assert result.status_code == 201, result.data
    assert len(client(regular).get("/api/v1/device-types/").data) == 1
    assert APIClient().get("/api/v1/device-types/").status_code in (401, 403)


@pytest.mark.django_db
def test_model_reused_by_devices_in_different_homes():
    dtype = DeviceType.objects.create(slug="camera", name="Câmera")
    model = DeviceModel.objects.create(device_type=dtype, manufacturer="X", model="Cam100")
    home1 = Home.objects.create(tenant=Tenant.objects.create(name="A"), name="A")
    home2 = Home.objects.create(tenant=Tenant.objects.create(name="B"), name="B")
    Device.objects.create(home=home1, device_model=model, name="Porta")
    Device.objects.create(home=home2, device_model=model, name="Garagem")
    assert Device.objects.filter(device_model=model).count() == 2


@pytest.mark.django_db
def test_image_upload_returns_url_and_serves_file(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    staff = User.objects.create_user(username="staff", email="staff@example.com", password="p", is_staff=True)
    dtype = DeviceType.objects.create(slug="camera", name="Câmera")
    data = io.BytesIO()
    Image.new("RGB", (2, 2)).save(data, format="PNG")
    upload = SimpleUploadedFile("camera.png", data.getvalue(), content_type="image/png")
    response = client(staff).post("/api/v1/device-models/", {
        "device_type": str(dtype.pk), "manufacturer": "X", "model": "Cam100",
        "image": upload,
    }, format="multipart")
    assert response.status_code == 201, response.data
    assert response.data["image_url"].endswith(f"/api/v1/device-models/{response.data['id']}/image/")
    image_response = APIClient().get(f"/api/v1/device-models/{response.data['id']}/image/")
    assert image_response.status_code == 200
    assert image_response["Content-Type"] == "image/png"
    assert b"".join(image_response.streaming_content).startswith(bytes([137, 80, 78, 71]))
