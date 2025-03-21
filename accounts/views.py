from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework import status

from accounts.authentication import authenticate_with_email
from accounts.serializers import ContactSerializer, UserSerializer
from accounts.models import Contact, User
from django.contrib.auth import authenticate


class SignUpView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        print("User:", request.user)
        print("Is Authenticated:", request.user.is_authenticated)

        contact_username = request.data.get('contact_username')  # Username of the contact to add
        phone_number = request.data.get('phone_number')  # Nomor HP dari request

        try:
            contact_user = User.objects.get(username=contact_username)
            if contact_user == request.user:
                return Response({'error': 'You cannot add yourself as a contact.'}, status=status.HTTP_400_BAD_REQUEST)

            contact, created = Contact.objects.get_or_create(user=request.user, contact=contact_user)
            if created:
                # Jika kontak baru dibuat, tambahkan nomor HP
                contact.phone_number = phone_number
                contact.save()
                return Response({'message': 'Contact added successfully.'}, status=status.HTTP_201_CREATED)
            else:
                # Jika kontak sudah ada, perbarui nomor HP jika diperlukan
                if phone_number:
                    contact.phone_number = phone_number
                    contact.save()
                return Response({'message': 'Contact already exists, phone number updated.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Contact user does not exist.'}, status=status.HTTP_404_NOT_FOUND)



class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_data = {
            'username': request.user.username,
            'email': request.user.email,
            'contacts': [
                {
                    'username': contact.contact.username,
                    'email': contact.contact.email,
                    'location': {
                        'latitude': contact.latitude,
                        'longitude': contact.longitude,
                        'city': contact.city,
                    } if contact.latitude and contact.longitude else None
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
