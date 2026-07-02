import os

from celery import Celery

# THIS MODULE WIRES CELERY TO DJANGO SETTINGS SO THE WORKER AND BEAT
# CONTAINERS CAN SHARE THE SAME CONFIGURATION AS THE WEB PROCESS.
#
# NOTE: DO NOT CALL django.setup() OR autodiscover_tasks(force=True) HERE.
# config/__init__.py IMPORTS celery_app FROM THIS MODULE, WHICH MEANS THIS
# MODULE RUNS AS A SIDE EFFECT OF IMPORTING config.settings ITSELF (PYTHON
# MUST EXECUTE config/__init__.py BEFORE config/settings.py). EAGERLY
# TOUCHING django.conf.settings/apps.populate() FROM HERE RE-ENTERS THAT
# SAME IMPORT CHAIN AND CORRUPTS THE APP REGISTRY. THE STANDARD DEFERRED
# FORM BELOW (NO force) IS THE PATTERN FROM CELERY'S OWN DJANGO INTEGRATION
# DOCS - DISCOVERY RUNS ON THE on_after_configure SIGNAL, AFTER DJANGO HAS
# FULLY FINISHED SETTING ITSELF UP.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

celery_app = Celery("devtracker")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()
