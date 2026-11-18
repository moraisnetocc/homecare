from django.db import transaction
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import Home, HomeMembership, Tenant, TenantMembership
from .permissions import AuthenticatedOnly, is_tenant_admin
from .serializers import (
    HomeMembershipSerializer, HomeSerializer,
    TenantMembershipSerializer, TenantSerializer,
)


class TenantListCreateView(generics.ListCreateAPIView):
    permission_classes = [AuthenticatedOnly]
    serializer_class = TenantSerializer

    def get_queryset(self):
        return Tenant.objects.filter(
            is_active=True, memberships__user=self.request.user
        ).distinct().order_by("created_at")

    @transaction.atomic
    def perform_create(self, serializer):
        tenant = serializer.save()
        TenantMembership.objects.create(
            tenant=tenant, user=self.request.user, role=TenantMembership.Role.OWNER
        )


class TenantDetailView(generics.RetrieveAPIView):
    permission_classes = [AuthenticatedOnly]
    serializer_class = TenantSerializer

    def get_queryset(self):
        return Tenant.objects.filter(
            is_active=True, memberships__user=self.request.user
        ).distinct()


class TenantMembershipListCreateView(generics.ListCreateAPIView):
    permission_classes = [AuthenticatedOnly]
    serializer_class = TenantMembershipSerializer

    def get_queryset(self):
        tenant_id = self.kwargs["tenant_id"]
        if not is_tenant_admin(self.request.user, tenant_id):
            raise PermissionDenied()
        return TenantMembership.objects.filter(tenant_id=tenant_id).order_by("created_at")

    def perform_create(self, serializer):
        tenant_id = self.kwargs["tenant_id"]
        if not is_tenant_admin(self.request.user, tenant_id):
            raise PermissionDenied()
        serializer.save(tenant_id=tenant_id)


class HomeListCreateView(generics.ListCreateAPIView):
    permission_classes = [AuthenticatedOnly]
    serializer_class = HomeSerializer

    def get_queryset(self):
        user = self.request.user
        return Home.objects.filter(tenant__is_active=True).filter(
            Q(memberships__user=user)
            | Q(tenant__memberships__user=user, tenant__memberships__role__in=[
                TenantMembership.Role.OWNER, TenantMembership.Role.ADMIN
            ])
        ).distinct().order_by("created_at")

    def perform_create(self, serializer):
        tenant = serializer.validated_data["tenant"]
        if not is_tenant_admin(self.request.user, tenant.pk):
            raise PermissionDenied()
        with transaction.atomic():
            home = serializer.save()
            HomeMembership.objects.create(
                home=home, user=self.request.user, role=HomeMembership.Role.OWNER
            )


class HomeDetailView(generics.RetrieveAPIView):
    permission_classes = [AuthenticatedOnly]
    serializer_class = HomeSerializer

    def get_queryset(self):
        user = self.request.user
        return Home.objects.filter(tenant__is_active=True).filter(
            Q(memberships__user=user)
            | Q(tenant__memberships__user=user, tenant__memberships__role__in=[
                TenantMembership.Role.OWNER, TenantMembership.Role.ADMIN
            ])
        ).distinct()


class HomeMembershipListCreateView(generics.ListCreateAPIView):
    permission_classes = [AuthenticatedOnly]
    serializer_class = HomeMembershipSerializer

    def _home(self):
        home = Home.objects.filter(pk=self.kwargs["home_id"], tenant__is_active=True).first()
        if home is None:
            from rest_framework.exceptions import NotFound
            raise NotFound()
        if not (
            is_tenant_admin(self.request.user, home.tenant_id)
            or HomeMembership.objects.filter(
                home=home, user=self.request.user, role=HomeMembership.Role.OWNER
            ).exists()
        ):
            raise PermissionDenied()
        return home

    def get_queryset(self):
        home = self._home()
        return HomeMembership.objects.filter(home=home).order_by("created_at")

    def perform_create(self, serializer):
        home = self._home()
        if not TenantMembership.objects.filter(
            tenant=home.tenant, user=serializer.validated_data["user"]
        ).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"user": "User must belong to the tenant."})
        serializer.save(home=home)
