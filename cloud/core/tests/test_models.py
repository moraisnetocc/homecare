import pytest
from django.db import IntegrityError, transaction
from core.models import User, Tenant, TenantMembership, Home, Installation

@pytest.mark.django_db
def test_tenant_membership_unique():
    user = User.objects.create_user(username="alice", email="alice@example.com", password="test-password-123")
    tenant = Tenant.objects.create(name="Tenant A")
    TenantMembership.objects.create(tenant=tenant, user=user, role="owner")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TenantMembership.objects.create(tenant=tenant, user=user, role="member")

@pytest.mark.django_db
def test_installation_is_one_per_home():
    tenant = Tenant.objects.create(name="Tenant A")
    home = Home.objects.create(tenant=tenant, name="Casa A")
    Installation.objects.create(home=home)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Installation.objects.create(home=home)

@pytest.mark.django_db
def test_tenants_have_separate_home_sets():
    a = Tenant.objects.create(name="A")
    b = Tenant.objects.create(name="B")
    home_a = Home.objects.create(tenant=a, name="Casa A")
    Home.objects.create(tenant=b, name="Casa B")
    assert list(Home.objects.filter(tenant=a)) == [home_a]
