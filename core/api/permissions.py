from rest_framework.permissions import BasePermission

from core.models import TenantMembership


def is_tenant_admin(user, tenant_id):
    return TenantMembership.objects.filter(
        user=user,
        tenant_id=tenant_id,
        tenant__is_active=True,
        role__in=[TenantMembership.Role.OWNER, TenantMembership.Role.ADMIN],
    ).exists()


class AuthenticatedOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)
