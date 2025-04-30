from django.urls import path
from .views import RegisterDeviceView, TrackingDataView, AccidentHistoryView, ContactRealtimeTrackingView, DevicePairingView, DeviceCredentialsView

urlpatterns = [
    path('devices/', RegisterDeviceView.as_view(), name='register_device'),
    path('location/', TrackingDataView.as_view(), name='tracking_data'),
    path('accidents/', AccidentHistoryView.as_view(), name='accident_history'),
    path('contacts_realtime/', ContactRealtimeTrackingView.as_view(), name='contacts_realtime'),
    path('credentials/', DeviceCredentialsView.as_view(),  name='device_credentials'),
    path('pairing/', DevicePairingView.as_view(), name='device_pairing'),
]