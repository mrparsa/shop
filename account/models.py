from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser): 
    phone = models.BigIntegerField(unique=True, null=True, blank=True, db_index=True)

    def __str__(self):
        return self.username 