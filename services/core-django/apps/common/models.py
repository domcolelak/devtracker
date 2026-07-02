from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    CUSTOM USER MODEL. WE SUBCLASS AbstractUser (RATHER THAN AbstractBaseUser)
    SINCE WE DO NOT NEED TO CHANGE THE AUTHENTICATION FIELD, ONLY EXTEND IT -
    THIS KEEPS DJANGO ADMIN AND PERMISSIONS WORKING OUT OF THE BOX WHILE STILL
    ALLOWING FUTURE FIELDS WITHOUT A COSTLY MIGRATION TO A NEW USER TABLE.
    """

    email = models.EmailField(unique=True)
    job_title = models.CharField(max_length=120, blank=True)
    avatar_url = models.URLField(blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self) -> str:
        return self.username
