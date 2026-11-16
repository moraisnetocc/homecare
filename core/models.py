import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F

class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)

class Tenant(UUIDModel):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.name

class TenantMembership(UUIDModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tenant_memberships")
    role = models.CharField(max_length=12, choices=Role.choices)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "user"], name="unique_tenant_user")]

class Home(UUIDModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="homes")
    name = models.CharField(max_length=200)
    timezone = models.CharField(max_length=64, default="America/Fortaleza")

class HomeMembership(UUIDModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        RESIDENT = "resident", "Resident"
        GUEST = "guest", "Guest"
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="home_memberships")
    role = models.CharField(max_length=12, choices=Role.choices)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["home", "user"], name="unique_home_user")]

class Installation(UUIDModel):
    home = models.OneToOneField(Home, on_delete=models.PROTECT, related_name="installation")
    last_seen_at = models.DateTimeField(null=True, blank=True)
    is_revoked = models.BooleanField(default=False)
