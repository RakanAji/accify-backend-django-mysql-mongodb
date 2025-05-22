from rest_framework import serializers
from django.contrib.auth import get_user_model

from accounts.models import Contact
import re

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phonenumber']
        extra_kwargs = {'password': {'write_only': True}, 'phonenumber': {'required': True}}
    
    # def validate_phonenumber(self, value):
    #     # Contoh: harus diawali +62 dan hanya angka setelahnya
        
    #     pattern = r'^\+62\d{8,13}$'
    #     if not re.match(pattern, value):
    #         raise serializers.ValidationError("Format nomor telepon tidak valid. Contoh: +6281234567890")
    #     return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phonenumber=validated_data.pop('phonenumber', None),
        )
        user.is_active = True
        user.save()
        return user


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['user', 'contact', 'phone_number', 'latitude', 'longitude', 'city', 'device_id']
        extra_kwargs = {'user': {'read_only': True}}
