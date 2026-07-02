"""
TEST-ONLY SETTINGS: SAME AS config.settings BUT WITH AN IN-MEMORY SQLITE
DATABASE (SO THE SUITE RUNS WITHOUT A POSTGRES INSTANCE), A LOCAL-MEMORY
EMAIL BACKEND (SO TESTS CAN INSPECT mail.outbox) AND A FAST PASSWORD HASHER.
"""

from config.settings import *  # noqa: F401,F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# MD5 IS DELIBERATE HERE: HASHING SPEED DOMINATES TEST RUNTIME AND THESE
# CREDENTIALS NEVER LEAVE THE TEST PROCESS
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# PLAIN STATIC FILE STORAGE - TESTS NEVER RUN collectstatic, AND THE MANIFEST
# BACKEND RAISES ON ANY {% static %} LOOKUP WITHOUT A MANIFEST FILE
STORAGES = {
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
