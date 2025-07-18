from django.urls import path
from .views import AddContactView, SignUpView, SignInView, SignOutView, UserDetailView, UpdateContactLocationView, UpdateFCMTokenView, DeleteContactView, VerifyOTPView, ResendOTPView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('verify_otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend_otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('signout/', SignOutView.as_view(), name='signout'),
    path('add_contact/', AddContactView.as_view(), name='add_contact'),
    path('contact_location/', UpdateContactLocationView.as_view(), name='contact_location'),
    path('me/', UserDetailView.as_view(), name='user_detail'),  # Endpoint untuk mengambil data user
    path('update_fcm_token/', UpdateFCMTokenView.as_view(), name='update_fcm_token'),
    path('delete_contact/', DeleteContactView.as_view(), name='delete_contact')
]
