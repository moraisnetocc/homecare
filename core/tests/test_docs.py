import pytest
from django.urls import reverse


def test_swagger_ui(client):
    response = client.get(reverse("swagger-ui"))
    assert response.status_code == 200


def test_redoc(client):
    response = client.get(reverse("redoc"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_openapi_schema_contains_routes(client):
    response = client.get(reverse("schema"), HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/tenants/" in paths
    assert "/api/v1/homes/" in paths
