import uuid
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q

class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Room",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("name", models.CharField(max_length=120)),
                ("home", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="rooms", to="core.home")),
            ],
        ),
        migrations.CreateModel(
            name="Device",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("name", models.CharField(max_length=160)),
                ("kind", models.CharField(choices=[("light", "Light"), ("outlet", "Outlet"), ("switch", "Switch"), ("sensor", "Sensor"), ("thermostat", "Thermostat"), ("other", "Other")], default="other", max_length=20)),
                ("external_id", models.CharField(blank=True, default="", max_length=255)),
                ("capabilities", models.JSONField(default=list)),
                ("state", models.JSONField(default=dict)),
                ("is_available", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("home", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="devices", to="core.home")),
                ("room", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="devices", to="core.room")),
            ],
        ),
        migrations.AddConstraint(model_name="room", constraint=models.UniqueConstraint(fields=("home", "name"), name="unique_room_name_per_home")),
        migrations.AddConstraint(model_name="device", constraint=models.UniqueConstraint(condition=~Q(external_id=""), fields=("home", "external_id"), name="unique_device_external_id_per_home")),
    ]
