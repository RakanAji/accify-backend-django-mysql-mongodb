from django.core.management.base import BaseCommand
import requests
import random
import time
from django.conf import settings

class Command(BaseCommand):
    help = 'Simulate IoT device sending location and accident data'
    
    def add_arguments(self, parser):
        parser.add_argument('--token', type=str, required=True, help='API token for authentication')
        parser.add_argument('--device', type=str, required=True, help='Device ID')
        parser.add_argument('--accident', action='store_true', help='Simulate accident')
        parser.add_argument('--interval', type=int, default=5, help='Interval in seconds between data points')
        
    def handle(self, *args, **options):
        token = options['token']
        device_id = options['device']
        simulate_accident = options['accident']
        interval = options['interval']
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        lat = -7.2575  
        lng = 112.7521
        speed = 0
        self.stdout.write(self.style.SUCCESS(f'Starting IoT simulation for device {device_id}'))
        try:
            for i in range(100):
                lat += random.uniform(-0.0005, 0.0005)
                lng += random.uniform(-0.0005, 0.0005)
                speed = max(0, speed + random.uniform(-5, 5))
                is_accident = simulate_accident and i == 10
                data = {
                    'device_id': device_id,
                    'latitude': lat,
                    'longitude': lng,
                    'speed': speed,
                    'is_accident': is_accident,
                    'additional_data': {
                        'battery': random.randint(50, 100),
                        'signal_strength': random.randint(1, 5)
                    }
                }
                url = 'http://localhost:8000/tracking/location/'
                response = requests.post(url, headers=headers, json=data)
                if response.status_code in (200, 201):
                    self.stdout.write(f'Data sent: {data}')
                    if is_accident:
                        self.stdout.write(self.style.WARNING('ACCIDENT DETECTED! Sending notifications...'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error sending data: {response.text}'))
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Simulation stopped by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in simulation: {e}'))
