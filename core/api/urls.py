from django.urls import path

from .views import (
    HomeDetailView, HomeListCreateView, HomeMembershipListCreateView,
    TenantDetailView, TenantListCreateView, TenantMembershipListCreateView,
)

urlpatterns = [
    path("tenants/", TenantListCreateView.as_view(), name="tenant-list"),
    path("tenants/<uuid:pk>/", TenantDetailView.as_view(), name="tenant-detail"),
    path("tenants/<uuid:tenant_id>/members/", TenantMembershipListCreateView.as_view(), name="tenant-members"),
    path("homes/", HomeListCreateView.as_view(), name="home-list"),
    path("homes/<uuid:pk>/", HomeDetailView.as_view(), name="home-detail"),
    path("homes/<uuid:home_id>/members/", HomeMembershipListCreateView.as_view(), name="home-members"),
]
