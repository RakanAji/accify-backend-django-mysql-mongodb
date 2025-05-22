from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    phonenumber = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True,
        help_text="Nomor telepon user (misalnya +6281234567890)"
    )

class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contacts")
    contact = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tracked_by")
    phone_number = models.CharField(max_length=15, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    device_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} -> {self.contact.username}"
