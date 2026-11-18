from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Tenant, TenantMembership, Home, HomeMembership, Installation, Room, Device, DeviceType, DeviceModel
admin.site.register(User, UserAdmin)
for model in (Tenant, TenantMembership, Home, HomeMembership, Installation):
    admin.site.register(model)
