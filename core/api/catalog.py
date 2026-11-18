from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import generics, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from core.models import DeviceType, DeviceModel
from .permissions import AuthenticatedOnly


class CatalogWriteStaffOnly(AuthenticatedOnly):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.method in ("GET", "HEAD", "OPTIONS") or request.user.is_staff
        )


def validate_capabilities(value):
    if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value):
        raise serializers.ValidationError("Expected a list of non-empty capability names.")
    return value


class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = ("id", "slug", "name", "created_at")
        read_only_fields = ("id", "created_at")


class DeviceModelSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = DeviceModel
        fields = ("id", "device_type", "manufacturer", "model", "protocol", "capabilities", "image", "image_url", "created_at")
        read_only_fields = ("id", "created_at", "image_url")

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        path = reverse("device-model-image", kwargs={"pk": obj.pk})
        return request.build_absolute_uri(path) if request else path

    def validate_capabilities(self, value):
        return validate_capabilities(value)

    def validate_image(self, value):
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image must be 5 MB or smaller.")
        return value


class DeviceTypeListCreateView(generics.ListCreateAPIView):
    permission_classes = [CatalogWriteStaffOnly]
    queryset = DeviceType.objects.all().order_by("name")
    serializer_class = DeviceTypeSerializer


class DeviceTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CatalogWriteStaffOnly]
    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer


class DeviceModelListCreateView(generics.ListCreateAPIView):
    permission_classes = [CatalogWriteStaffOnly]
    queryset = DeviceModel.objects.select_related("device_type").order_by("manufacturer", "model")
    serializer_class = DeviceModelSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]


class DeviceModelDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CatalogWriteStaffOnly]
    queryset = DeviceModel.objects.select_related("device_type")
    serializer_class = DeviceModelSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def device_model_image(request, pk):
    device_model = get_object_or_404(DeviceModel, pk=pk)
    if not device_model.image:
        raise Http404
    try:
        return FileResponse(device_model.image.open("rb"), content_type="image/" + device_model.image.name.rsplit(".", 1)[-1].lower())
    except (FileNotFoundError, OSError):
        raise Http404
