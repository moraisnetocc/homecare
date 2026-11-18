from django.db.models import Q
from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied

from core.models import Device, Home, HomeMembership, Room, TenantMembership
from .permissions import AuthenticatedOnly, is_tenant_admin


def visible_homes(user):
    return Home.objects.filter(tenant__is_active=True).filter(
        Q(memberships__user=user)
        | Q(tenant__memberships__user=user, tenant__memberships__role__in=[
            TenantMembership.Role.OWNER, TenantMembership.Role.ADMIN
        ])
    ).distinct()


def writable_homes(user):
    return Home.objects.filter(tenant__is_active=True).filter(
        Q(memberships__user=user, memberships__role=HomeMembership.Role.OWNER)
        | Q(tenant__memberships__user=user, tenant__memberships__role__in=[
            TenantMembership.Role.OWNER, TenantMembership.Role.ADMIN
        ])
    ).distinct()


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ("id", "home", "name", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_home(self, value):
        if not visible_homes(self.context["request"].user).filter(pk=value.pk).exists():
            raise serializers.ValidationError("Home not found.")
        return value

    def validate(self, attrs):
        home = attrs.get("home", getattr(self.instance, "home", None))
        if home and Room.objects.filter(home=home, name=attrs.get("name", getattr(self.instance, "name", None))).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError({"name": "Room name already exists in this home."})
        return attrs


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ("id", "home", "room", "name", "kind", "external_id", "capabilities", "state", "is_available", "created_at", "updated_at")
        read_only_fields = ("id", "state", "is_available", "created_at", "updated_at")

    def validate_home(self, value):
        if not visible_homes(self.context["request"].user).filter(pk=value.pk).exists():
            raise serializers.ValidationError("Home not found.")
        return value

    def validate(self, attrs):
        home = attrs.get("home", getattr(self.instance, "home", None))
        room = attrs.get("room", getattr(self.instance, "room", None))
        if room is not None and home is not None and room.home_id != home.pk:
            raise serializers.ValidationError({"room": "Room must belong to the selected home."})
        capabilities = attrs.get("capabilities", getattr(self.instance, "capabilities", []))
        if not isinstance(capabilities, list) or not all(isinstance(item, str) and item for item in capabilities):
            raise serializers.ValidationError({"capabilities": "Expected a list of capability names."})
        external_id = attrs.get("external_id", getattr(self.instance, "external_id", ""))
        if home and external_id and Device.objects.filter(home=home, external_id=external_id).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError({"external_id": "External ID already exists in this home."})
        return attrs


class HomeScopedAccessMixin:
    permission_classes = [AuthenticatedOnly]

    def get_queryset(self):
        return self.model.objects.filter(home__in=visible_homes(self.request.user)).order_by("created_at")

    def perform_create(self, serializer):
        home = serializer.validated_data["home"]
        if not writable_homes(self.request.user).filter(pk=home.pk).exists():
            raise PermissionDenied("Only home owners and tenant admins may modify resources.")
        serializer.save()

    def perform_update(self, serializer):
        home = serializer.validated_data.get("home", serializer.instance.home)
        if not writable_homes(self.request.user).filter(pk=serializer.instance.home_id).exists() or not writable_homes(self.request.user).filter(pk=home.pk).exists():
            raise PermissionDenied("Only home owners and tenant admins may modify resources.")
        serializer.save()

    def perform_destroy(self, instance):
        if not writable_homes(self.request.user).filter(pk=instance.home_id).exists():
            raise PermissionDenied("Only home owners and tenant admins may modify resources.")
        instance.delete()


class RoomListCreateView(HomeScopedAccessMixin, generics.ListCreateAPIView):
    serializer_class = RoomSerializer
    model = Room

    def get_queryset(self):
        queryset = super().get_queryset()
        home_id = self.request.query_params.get("home")
        return queryset.filter(home_id=home_id) if home_id else queryset


class RoomDetailView(HomeScopedAccessMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RoomSerializer
    model = Room


class DeviceListCreateView(HomeScopedAccessMixin, generics.ListCreateAPIView):
    serializer_class = DeviceSerializer
    model = Device

    def get_queryset(self):
        queryset = super().get_queryset()
        home_id = self.request.query_params.get("home")
        return queryset.filter(home_id=home_id) if home_id else queryset


class DeviceDetailView(HomeScopedAccessMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DeviceSerializer
    model = Device
