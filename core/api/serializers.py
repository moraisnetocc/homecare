from rest_framework import serializers

from core.models import Home, HomeMembership, Tenant, TenantMembership, User


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ("id", "name", "is_active", "created_at")
        read_only_fields = ("id", "is_active", "created_at")


class TenantMembershipSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))

    class Meta:
        model = TenantMembership
        fields = ("id", "tenant", "user", "role", "created_at")
        read_only_fields = ("id", "tenant", "created_at")

    def validate_role(self, value):
        if value == TenantMembership.Role.OWNER:
            raise serializers.ValidationError("Owner transfers are not supported by this endpoint.")
        return value


class HomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Home
        fields = ("id", "tenant", "name", "timezone", "created_at")
        read_only_fields = ("id", "created_at")


class HomeMembershipSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))

    class Meta:
        model = HomeMembership
        fields = ("id", "home", "user", "role", "created_at")
        read_only_fields = ("id", "home", "created_at")

    def validate_role(self, value):
        if value == HomeMembership.Role.OWNER:
            raise serializers.ValidationError("Home owner transfers are not supported by this endpoint.")
        return value
