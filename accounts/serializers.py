from rest_framework import serializers
from django.contrib.auth import get_user_model

from accounts.models import Contact

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.is_active = True
        user.save()
        return user


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['user', 'contact', 'phone_number', 'latitude', 'longitude', 'city']
        extra_kwargs = {'user': {'read_only': True}}
