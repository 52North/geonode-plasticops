
from django.apps import AppConfig

import logging
logger = logging.getLogger(__name__)


def run_setup_hooks(*args, **kwargs):
    from django.conf import settings

    settings.MAPSTORE_TRANSLATIONS_PATH += (
        "/static/mapstore/ea-translations",
    )


class LitterAssessmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'litter_assessment'
    type = 'GEONODE_APP'

    def ready(self):
        super().ready()
        run_setup_hooks()


default_app_config = 'litter_assessment.LitterAssessmentConfig'
