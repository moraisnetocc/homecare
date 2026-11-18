import uuid
import django.db.models.deletion
from django.db import migrations, models
import core.models


class Migration(migrations.Migration):
    dependencies = [("core", "0002_room_device")]

    operations = [
        migrations.CreateModel(
            name="DeviceType",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("name", models.CharField(max_length=120)),
            ],
        ),
        migrations.CreateModel(
            name="DeviceModel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("manufacturer", models.CharField(max_length=120)),
                ("model", models.CharField(max_length=160)),
                ("protocol", models.CharField(blank=True, default="", max_length=80)),
                ("capabilities", models.JSONField(default=list)),
                ("image", models.ImageField(blank=True, null=True, upload_to=core.models.device_model_image_path)),
                ("device_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="models", to="core.devicetype")),
            ],
        ),
        migrations.AddField(
            model_name="device",
            name="device_model",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="devices", to="core.devicemodel"),
        ),
        migrations.AddConstraint(
            model_name="devicemodel",
            constraint=models.UniqueConstraint(fields=("manufacturer", "model", "protocol"), name="unique_catalog_device_model"),
        ),
    ]
