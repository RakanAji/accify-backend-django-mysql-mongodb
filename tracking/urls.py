from django.urls import path
from .views import RegisterDeviceView, TrackingDataView, AccidentHistoryView

urlpatterns = [
    path('devices/', RegisterDeviceView.as_view(), name='register_device'),
    path('location/', TrackingDataView.as_view(), name='tracking_data'),
    path('accidents/', AccidentHistoryView.as_view(), name='accident_history'),
]