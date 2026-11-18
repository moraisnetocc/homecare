from django.urls import path
from .views import (
    HomeDetailView, HomeListCreateView, HomeMembershipListCreateView,
    TenantDetailView, TenantListCreateView, TenantMembershipListCreateView,
)
from .resources import RoomListCreateView, RoomDetailView, DeviceListCreateView, DeviceDetailView
from .catalog import DeviceTypeListCreateView, DeviceTypeDetailView, DeviceModelListCreateView, DeviceModelDetailView, device_model_image

urlpatterns = [
    path("tenants/", TenantListCreateView.as_view(), name="tenant-list"),
    path("tenants/<uuid:pk>/", TenantDetailView.as_view(), name="tenant-detail"),
    path("tenants/<uuid:tenant_id>/members/", TenantMembershipListCreateView.as_view(), name="tenant-members"),
    path("homes/", HomeListCreateView.as_view(), name="home-list"),
    path("homes/<uuid:pk>/", HomeDetailView.as_view(), name="home-detail"),
    path("homes/<uuid:home_id>/members/", HomeMembershipListCreateView.as_view(), name="home-members"),
    path("device-types/", DeviceTypeListCreateView.as_view(), name="device-type-list"),
    path("device-types/<uuid:pk>/", DeviceTypeDetailView.as_view(), name="device-type-detail"),
    path("device-models/", DeviceModelListCreateView.as_view(), name="device-model-list"),
    path("device-models/<uuid:pk>/", DeviceModelDetailView.as_view(), name="device-model-detail"),
    path("device-models/<uuid:pk>/image/", device_model_image, name="device-model-image"),
    path("rooms/", RoomListCreateView.as_view(), name="room-list"),
    path("rooms/<uuid:pk>/", RoomDetailView.as_view(), name="room-detail"),
    path("devices/", DeviceListCreateView.as_view(), name="device-list"),
    path("devices/<uuid:pk>/", DeviceDetailView.as_view(), name="device-detail"),
]
