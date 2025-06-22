from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework import status

from accounts.authentication import authenticate_with_email
from accounts.serializers import ContactSerializer, UserSerializer
from accounts.models import Contact, User
from django.contrib.auth import authenticate
from .utils import generate_otp, send_otp_email, store_signup_data, retrieve_signup_data
from django.core.cache import cache

from tracking.serializers import IoTDeviceSerializer
from tracking.models import IoTDevice


class SignUpView(APIView):
    permission_classes = [AllowAny] # Izinkan siapa saja untuk signup

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            # Cek apakah user sudah ada dan aktif
            if User.objects.filter(email=email, is_active=True).exists():
                return Response({'error': 'Email ini sudah terdaftar dan aktif.'}, status=status.HTTP_400_BAD_REQUEST)

            otp = generate_otp()
            if send_otp_email(email, otp):
                # Simpan data & OTP di cache
                store_signup_data(email, serializer.validated_data, otp)
                return Response(
                    {'message': f'OTP telah dikirim ke {email}. Silakan verifikasi.'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Gagal mengirim OTP. Silakan coba lagi.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp_input = request.data.get('otp')

        if not email or not otp_input:
            return Response({'error': 'Email dan OTP diperlukan.'}, status=status.HTTP_400_BAD_REQUEST)

        user_data = retrieve_signup_data(email, otp_input)

        if user_data:
            # Data valid, buat user sekarang
            try:
                # Gunakan UserSerializer lagi untuk membuat user
                serializer = UserSerializer(data=user_data)
                serializer.is_valid(raise_exception=True) # Seharusnya valid
                user = serializer.save()
                # Pastikan user diaktifkan
                user.is_active = True
                user.save()

                token, _ = Token.objects.get_or_create(user=user)
                return Response({'token': token.key, 'message': 'Akun berhasil diverifikasi dan dibuat.'}, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Tangani jika ada error saat membuat user (misalnya email sudah ada_
                print(f"Error creating user after OTP verify: {e}")
                return Response({'error': 'Terjadi kesalahan saat membuat akun.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'error': 'OTP salah atau sudah kedaluwarsa.'}, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    """
    Handles requests to resend the OTP code during signup.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        signup_key = f"signup_{email}"
        cooldown_key = f"resend_cooldown_{email}"

        # 1. Cek apakah ada data signup yang pending
        user_data_cache = cache.get(signup_key)
        if not user_data_cache:
            return Response({'error': 'No pending registration found or it has expired.'},
                            status=status.HTTP_404_NOT_FOUND)

        # 2. Cek Cooldown (misalnya 60 detik)
        if cache.get(cooldown_key):
            return Response({'error': 'Please wait 60 seconds before requesting a new OTP.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)

        # 3. Generate & Kirim OTP Baru
        user_data = user_data_cache.get('data') # Ambil data user asli
        new_otp = generate_otp()

        if send_otp_email(email, new_otp):
            # 4. Simpan ulang data dengan OTP baru (dan reset timeout cache)
            store_signup_data(email, user_data, new_otp) # Timeout 10 menit lagi
            # 5. Set Cooldown
            cache.set(cooldown_key, True, timeout=60) # Set cooldown 60 detik

            return Response({'message': 'A new OTP has been sent to your email.'},
                            status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Failed to send new OTP. Please try again later.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate_with_email(email=email, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    


class SignOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)



class AddContactView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        contact_username = request.data.get('contact_username')
        phone_number = request.data.get('phone_number')
        # Ini adalah device_id yang dimasukkan user B untuk user A
        device_id_for_A = request.data.get('device_id') 

        try:
            # 1. Cari User A (contact_user)
            contact_user = User.objects.get(username=contact_username, phonenumber=phone_number)
            
            if contact_user == request.user:
                return Response(
                    {'error': 'You cannot add yourself as a contact.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Validasi device_id_for_A (jika dimasukkan)
            validated_device_id = None # Default None jika dikosongkan
            if device_id_for_A:
                try:
                    device = IoTDevice.objects.get(device_id=device_id_for_A)
                    # Cek kepemilikan
                    if device.user != contact_user:
                        return Response(
                            {'error': f'Device ID {device_id_for_A} does not belong to user {contact_username}.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    # Cek pairing
                    if not device.device_token:
                        return Response(
                            {'error': f'Device ID {device_id_for_A} has not been paired yet.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    # Jika lolos validasi
                    validated_device_id = device_id_for_A
                except IoTDevice.DoesNotExist:
                    return Response(
                        {'error': f'Device ID {device_id_for_A} not found.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # 3. Buat atau perbarui kontak B -> A
            contact, created = Contact.objects.get_or_create(
                user=request.user,
                contact=contact_user,
                defaults={'phone_number': phone_number, 'device_id': validated_device_id}
            )
            # Jika sudah ada, update datanya
            if not created:
                contact.phone_number = phone_number
                contact.device_id = validated_device_id
                contact.save()

            # 4. Siapkan dan buat/perbarui kontak balik A -> B
            userB_phone = request.user.phonenumber
            # Cari device milik User B yang sudah pairing (ambil yang terakhir)
            userB_device = IoTDevice.objects.filter(user=request.user, device_token__isnull=False).last()
            userB_device_id = userB_device.device_id if userB_device else None

            reverse_contact, reverse_created = Contact.objects.get_or_create(
                user=contact_user,
                contact=request.user,
                defaults={'phone_number': userB_phone, 'device_id': userB_device_id}
            )
            # Jika sudah ada, update datanya
            if not reverse_created:
                reverse_contact.phone_number = userB_phone
                reverse_contact.device_id = userB_device_id
                reverse_contact.save()

            # 5. Berikan response sukses
            return Response(
                {'message': 'Contact added successfully and mutual contact created/updated.'},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {'error': 'Contact user does not exist. Check the username and phone number.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Tangkap error tak terduga untuk debugging
            print(f"Unexpected error in AddContactView: {e}")
            return Response({'error': 'An internal server error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteContactView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        contact_username = request.data.get('contact_username')
        
        if not contact_username:
            return Response({'error': 'Contact username is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            contact_user = User.objects.get(username=contact_username)
        except User.DoesNotExist:
            return Response({'error': 'Contact user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        # Hapus kontak userA -> userB
        Contact.objects.filter(user=request.user, contact=contact_user).delete()
        
        # Hapus kontak balik userB -> userA
        Contact.objects.filter(user=contact_user, contact=request.user).delete()
        
        return Response({'message': 'Contact deleted successfully'}, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token, _ = Token.objects.get_or_create(user=request.user)
        user_data = {
            'username': request.user.username,
            'email': request.user.email,
            'auth_token': token.key,
            'contacts': [
                {
                    'username': contact.contact.username,
                    'email': contact.contact.email,
                    'phonenumber': contact.contact.phonenumber,
                    'device_id': contact.device_id,
                    
                }
                for contact in request.user.contacts.all()
            ],
        }
        return Response(user_data, status=status.HTTP_200_OK)
    
class UpdateContactLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Ambil data dari request
        contact_username = request.data.get('contact_username')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        city = request.data.get('city')  # opsional, jika ada

        if not (contact_username and latitude and longitude):
            return Response({'error': 'Incomplete data. Username, latitude, and longitude are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Pastikan kontak yang dimaksud adalah milik user yang sedang login
            contact = Contact.objects.get(user=request.user, contact__username=contact_username)
            contact.latitude = latitude
            contact.longitude = longitude
            contact.city = city  # bisa null jika tidak dikirim
            contact.save()
            return Response({'message': 'Location updated successfully.'}, status=status.HTTP_200_OK)
        except Contact.DoesNotExist:
            return Response({'error': 'Contact not found.'}, status=status.HTTP_404_NOT_FOUND)

class UpdateFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('fcm_token')
        if token:
            request.user.fcm_token = token
            request.user.save()
            return Response({'message': 'FCM token updated successfully.'}, status=200)
        return Response({'error': 'No FCM token provided.'}, status=400)