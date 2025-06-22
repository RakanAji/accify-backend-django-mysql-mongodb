# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from accounts.models import User
# from tracking.models import IoTDevice

# @receiver(post_save, sender=User)
# def create_iot_device(sender, instance, created, **kwargs):
#     if created:
#         # Format device id: Accify_{username}
#         device_id = f"Accify_{instance.username}"
#         # Cek apakah device dengan device id tersebut sudah ada (meskipun seharusnya belum)
#         if not IoTDevice.objects.filter(device_id=device_id).exists():
#             IoTDevice.objects.create(
#                 user=instance,
#                 device_id=device_id,
#                 name=f"Device {instance.username}"
#             )
