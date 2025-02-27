import logging
from django.db import migrations
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Permission

from geonode.groups.models import GroupProfile

logger = logging.getLogger(__name__)

def update_group_access(apps, schema_editor):
    group_profile, create = GroupProfile.objects.get_or_create(
        slug="ai-inference"
    )
    group_profile.access = "public-invite"
    group_profile.save()


class Migration(migrations.Migration):
    dependencies = [
        ("groups", "__latest__"),
        ("litterassessment", "0003_inference"),
    ]

    operations = [
        migrations.RunPython(update_group_access),
    ]