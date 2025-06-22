from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework import status
from .models import IoTDevice, MongoDBManager
from .serializers import IoTDeviceSerializer, LocationDataSerializer, AccidentSerializer
from .authentication import DeviceTokenAuthentication
from accounts.models import Contact, User
from django.shortcuts import get_object_or_404
import json
from firebase_admin import messaging
import firebase_admin
from firebase_admin import credentials
import os
from django.conf import settings
import requests
import uuid
from django.utils import timezone
import datetime

# Inisialisasi Firebase untuk notifikasi (Anda perlu menambahkan konfigurasi ini)
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(os.path.join(settings.BASE_DIR, 'firebase-credentials.json'))
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Error initializing Firebase: {e}")

# Hardcoded mapping of ephemeral_id to pairing_code
PAIRING_CODE_MAPPING = {
    "B46A3665B7A0": "ACPAIR2025",
    "B46A3665B7A1": "ACPAIR2026",
    "B46A3665B7A2": "ACPAIR2027",
    # Tambahkan lebih banyak pasangan ephemeral_id dan pairing_code di sini jika perlu
}

class DevicePairingView(APIView):
    """
    User memasukkan ephemeral_id & pairing_code lewat mobile app.
    - Kalau pairing pertama (ephemeral_id baru): generate device_id + device_token, simpan record.
    - Kalau pairing ulang (ephemeral_id sama): reuse device_id dari record, generate device_token baru, update record.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ephemeral_id = request.data.get('ephemeral_id')
        pairing_code = request.data.get('pairing_code')

        # Validasi ephemeral_id ada dalam mapping
        if ephemeral_id not in PAIRING_CODE_MAPPING:
            return Response({'error': 'Invalid ephemeral ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Validasi pairing_code sesuai dengan ephemeral_id
        if pairing_code != PAIRING_CODE_MAPPING[ephemeral_id]:
            return Response({'error': 'Invalid pairing code for this ephemeral ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Coba-cari record yang sudah ada untuk ephemeral_id ini
        try:
            device = IoTDevice.objects.get(ephemeral_id=ephemeral_id)
            # Kalau ketemu, generate token baru saja (device_id tetap sama)
            new_token = uuid.uuid4().hex
            device.device_token = new_token
            device.user = request.user       # ← opsional: jika ingin catat user terakhir yang pairing
            device.name = f"Device {request.user.username}"  # ← opsional: update nama device
            device.save(update_fields=['device_token', 'user', 'name'])

            return Response({
                'device_id':    device.device_id,  # gunakan device_id lama
                'device_token': new_token
            }, status=status.HTTP_200_OK)

        except IoTDevice.DoesNotExist:
            # Kalau belum ada record, ini pairing pertama
            final_device_id = "Accify_" + uuid.uuid4().hex[:12].upper()
            new_token       = uuid.uuid4().hex

            device = IoTDevice.objects.create(
                ephemeral_id=ephemeral_id,
                user=request.user,
                device_id=final_device_id,
                device_token=new_token,
                name=f"Device {request.user.username}"
            )
            return Response({
                'device_id':    final_device_id,
                'device_token': new_token
            }, status=status.HTTP_201_CREATED)

class DeviceCredentialsView(APIView):
    """
    Dipanggil ESP32 tanpa auth header.
    Input: ephemeral_id + pairing_code.
    Output: device_id + device_token (jika sudah dipairing oleh user).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        ephemeral_id = request.data.get('ephemeral_id')
        pairing_code = request.data.get('pairing_code')

        # Validasi ephemeral_id ada dalam mapping
        if ephemeral_id not in PAIRING_CODE_MAPPING:
            return Response({'error': 'Invalid ephemeral ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Validasi pairing_code sesuai dengan ephemeral_id
        if pairing_code != PAIRING_CODE_MAPPING[ephemeral_id]:
            return Response({'error': 'Invalid pairing code for this ephemeral ID'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = IoTDevice.objects.get(ephemeral_id=ephemeral_id)
        except IoTDevice.DoesNotExist:
            return Response({'error': 'Device not registered by any user yet'},
                            status=status.HTTP_404_NOT_FOUND)

        if not device.device_token:
            return Response({'error': 'Device not paired by user yet'},
                            status=status.HTTP_409_CONFLICT)

        return Response({
            'device_id':    device.device_id,
            'device_token': device.device_token
        }, status=status.HTTP_200_OK)

class RegisterDeviceView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = IoTDeviceSerializer(data=request.data)
        if serializer.is_valid():
            device, created = IoTDevice.objects.update_or_create(
                device_id=serializer.validated_data['device_id'],
                defaults={'user': request.user, 'name': serializer.validated_data.get('name', '')}
            )
            return Response(IoTDeviceSerializer(device).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        devices = IoTDevice.objects.filter(user=request.user)
        serializer = IoTDeviceSerializer(devices, many=True)
        return Response(serializer.data)

class TrackingDataView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LocationDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Karena valid, request.user sudah = pemilik IoTDevice
        device_id = serializer.validated_data['device_id']
        # Pastikan device_id sesuai dengan device yang authenticated
        if request.iot_device.device_id != device_id:
            return Response(
                {'error': 'Device ID mismatch'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Simpan data ke MongoDB
        mongo_manager = MongoDBManager()
        inserted_id = mongo_manager.save_location_data(
            device_id, 
            serializer.validated_data
        )
            
        # Jika terjadi kecelakaan, kirim notifikasi
        if serializer.validated_data.get('is_accident', False):
            self._send_accident_notification(request.user, serializer.validated_data)
        
        return Response(
            {'message': 'Location data saved', 'id': str(inserted_id)},
            status=status.HTTP_201_CREATED
        )
    
    def get(self, request):
        device_id = request.query_params.get('device_id')
        if not device_id:
            return Response(
                {'error': 'device_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verifikasi bahwa device milik user yang terautentikasi
        try:
            device = IoTDevice.objects.get(device_id=device_id, user=request.user)
        except IoTDevice.DoesNotExist:
            return Response(
                {'error': 'Device not found or you do not have permission'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Ambil data lokasi terbaru dari MongoDB
        mongo_manager = MongoDBManager()
        recent_data = mongo_manager.get_recent_location(device_id, limit=20)
        
        # Konversi ObjectId menjadi string untuk serialisasi JSON
        for data in recent_data:
            data['_id'] = str(data['_id'])
        
        return Response(recent_data)
    
    def _send_accident_notification(self, user, accident_data):
        """
        Mengirim notifikasi kecelakaan ke orang terdekat dan rumah sakit terdekat
        """
        # Ambil daftar kontak user
        contacts = Contact.objects.filter(user=user)
        
        # Dapatkan informasi kecelakaan
        lat = accident_data.get('latitude')
        lng = accident_data.get('longitude')
        
        # Persiapkan pesan notifikasi
        accident_message = {
            'title': 'EMERGENCY: Accident Detected!',
            'body': f'Your contact {user.username} has been detected in an accident.',
            'data': {
                'latitude': str(lat),
                'longitude': str(lng),
                'user_id': str(user.id),
                'type': 'accident'
            }
        }
        
        # Kirim notifikasi ke setiap kontak yang terdaftar
        for contact in contacts:
            # Di sini Anda perlu implementasi untuk mengirim notifikasi
            # Bisa menggunakan Firebase Cloud Messaging atau platform notifikasi lainnya
            # Untuk contoh, saya menggunakan metode placeholder
            try:
                # Jika Anda memiliki token Firebase untuk user, gunakan ini
                # Asumsi: token FCM disimpan di profil user (Anda perlu menambahkan ini)
                if hasattr(contact.contact, 'fcm_token') and contact.contact.fcm_token:
                    print(f"FCM TOKEN BERHASIL")
                    self._send_fcm_notification(contact.contact.fcm_token, accident_message)
                    
                
                # Kirim SMS ke nomor telepon kontak jika ada
                if contact.phone_number:
                    self._send_sms_notification(contact.phone_number, 
                        f"EMERGENCY: {user.username} has been detected in an accident at " +
                        f"coordinates: {lat}, {lng}"
                    )
            except Exception as e:
                print(f"Error sending notification to contact {contact.contact.username}: {e}")
        
        # Cari rumah sakit terdekat dan kirim notifikasi
        self._notify_nearest_hospital(lat, lng, user)
    
    def _send_fcm_notification(self, token, message_dict):
        """
        Kirim notifikasi via Firebase Cloud Messaging.
        message_dict = {
            'title': 'EMERGENCY: Accident Detected!',
            'body': 'Your contact ... detected an accident.',
            'data': { ... }  # opsional, kalau ingin kirim data tambahan
        }
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=message_dict['title'],
                    body=message_dict['body'],
                ),
                data=message_dict.get('data', {}),
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',                    # Penting: high priority
                    notification=messaging.AndroidNotification(
                        channel_id='accident_alerts',   # ID channel (bisa apa saja, nanti kita buat di React Native)
                        sound='default',                # Putar suara notifikasi default
                        click_action='FLUTTER_NOTIFICATION_CLICK'  # atau action apapun
                    )
                ),
                apns=messaging.APNSConfig(
                    headers={'apns-priority': '10'},    # untuk iOS, kalau nanti dibutuhkan
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            content_available=True            # biar iOS juga kebangun
                        )
                    )
                )
            )
            response = messaging.send(message)
            print(f"FCM notification sent: {response}")
            return True
        except Exception as e:
            print(f"Error sending FCM notification: {e}")
            return False
    
    def _send_sms_notification(self, phone_number, message):
        """
        Placeholder untuk kirim SMS (Anda perlu implementasi sesuai provider)
        """
        # Implementasikan integrasi dengan layanan SMS seperti Twilio
        print(f"SMS sent to {phone_number}: {message}")
        # Contoh dengan Twilio (Anda perlu tambahkan kredensial)
        # from twilio.rest import Client
        # client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # client.messages.create(body=message, from_=TWILIO_PHONE, to=phone_number)
        return True
    
    def _notify_nearest_hospital(self, lat, lng, user):
        """
        Mencari rumah sakit terdekat dan mengirim notifikasi
        """
        # Implementasi untuk mencari rumah sakit terdekat
        # Bisa menggunakan Google Maps API atau layanan sejenis
        
        # Placeholder
        print(f"Notifying nearest hospital for accident at {lat}, {lng}")
        
        # Contoh menggunakan API Places dari Google (Anda perlu API key)
        # api_key = settings.GOOGLE_MAPS_API_KEY
        # url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&type=hospital&key={api_key}"
        # response = requests.get(url)
        # hospitals = response.json().get('results', [])
        
        # if hospitals:
        #     nearest = hospitals[0]
        #     hospital_name = nearest.get('name')
        #     hospital_phone = nearest.get('formatted_phone_number')
        #     # Kirim notifikasi ke rumah sakit...
        
        return True

class AccidentHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all accident history for user's devices"""
        # Ambil semua device milik user
        devices = IoTDevice.objects.filter(user=request.user)
        device_ids = [device.device_id for device in devices]
        
        # Jika tidak ada device, return empty list
        if not device_ids:
            return Response([])
        
        # Ambil data kecelakaan dari MongoDB berdasarkan device ids
        mongo_manager = MongoDBManager()
        accidents = []
        
        for device_id in device_ids:
            device_accidents = mongo_manager.get_accident_data(device_id)
            # Konversi ObjectId ke string
            for accident in device_accidents:
                accident['_id'] = str(accident['_id'])
            accidents.extend(device_accidents)
        
        # Sort berdasarkan timestamp
        accidents.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return Response(accidents)
    
class ContactRealtimeTrackingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Mengembalikan daftar kontak user beserta data realtime (lokasi, kecepatan) yang diambil dari MongoDB.
        User harus memiliki kontak yang sudah terdaftar dengan device_id.
        """
        # Ambil daftar kontak user dari MySQL
        contacts = Contact.objects.filter(user=request.user)
        mongo_manager = MongoDBManager()
        result = []

        

        for contact in contacts:
            # Pastikan kontak memiliki device_id
            if not contact.device_id:
                continue

            # Ambil data realtime dari MongoDB berdasarkan device_id kontak
            realtime_data = mongo_manager.get_recent_location(contact.device_id, limit=1)
            if realtime_data:
                # Ambil data terbaru (misalnya, data pertama dari list)
                data = realtime_data[0]
                # Ubah ObjectId ke string jika diperlukan
                data['_id'] = str(data['_id'])

                
            else:
                data = None

            result.append({
                'contact_username': contact.contact.username,
                'contact_email': contact.contact.email,
                'phone_number': contact.phone_number,
                'device_id': contact.device_id,
                'realtime_data': data  # bisa berisi latitude, longitude, speed, timestamp, dsb.
            })

        return Response(result, status=status.HTTP_200_OK)