# tracking/authentication.py

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions
from .models import IoTDevice

class DeviceTokenAuthentication(BaseAuthentication):
    """
    Authenticate an IoTDevice by its device_token.
    If valid, set request.user = device.user
    """
    keyword = 'Token'

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None  # lanjut ke auth lain (atau fail kalau hanya pakai ini)
        if len(auth) != 2:
            raise exceptions.AuthenticationFailed('Invalid Authorization header format')
        token = auth[1].decode()
        try:
            device = IoTDevice.objects.get(device_token=token, is_active=True)
        except IoTDevice.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid device token')
        # Pasang device dan user ke request
        request.iot_device = device
        return (device.user, None)
