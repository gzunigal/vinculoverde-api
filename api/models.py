from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

class Organization(models.Model):
  name = models.CharField(max_length=100)
  short_name = models.CharField(max_length=30, null=True)
  address = models.CharField(max_length=150)
  phone = models.CharField(max_length=35)
  email = models.CharField(max_length=100)


class User(AbstractUser):
  national_id = models.CharField(max_length=30, null=False, unique=True, blank=False)
  supervised_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
  organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True)
  address = models.CharField(max_length=150)
  phone = models.CharField(max_length=35)
  age = models.IntegerField(null=True)
  gender = models.CharField(max_length=30, null=True)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
  print("trigger")
  if created:
    print("tringger when created")
    Token.objects.create(user=instance)


