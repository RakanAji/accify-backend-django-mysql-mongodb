# accounts/utils.py
import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache

def generate_otp(length=6):
    """Menghasilkan OTP numerik acak."""
    return str(random.randint(10**(length-1), (10**length)-1))

def send_otp_email(email, otp):
    """Mengirim OTP ke alamat email yang diberikan."""
    subject = 'Kode Verifikasi Akun Accify Anda'
    message = f'Gunakan kode ini untuk memverifikasi akun Anda: {otp}\nKode ini valid selama 10 menit.'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email,]
    try:
        send_mail(subject, message, email_from, recipient_list)
        return True
    except Exception as e:
        print(f"Gagal mengirim email OTP ke {email}: {e}") # Tambahkan logging yang lebih baik
        return False

def store_signup_data(email, data, otp, timeout_minutes=10):
    """Menyimpan data signup dan OTP di cache."""
    cache_key = f"signup_{email}"
    cache_data = {'data': data, 'otp': otp}
    cache.set(cache_key, cache_data, timeout=timeout_minutes * 60)

def retrieve_signup_data(email, otp_input):
    """Mengambil data signup jika OTP cocok."""
    cache_key = f"signup_{email}"
    cached = cache.get(cache_key)
    if cached and cached.get('otp') == otp_input:
        cache.delete(cache_key) # Hapus setelah berhasil
        return cached.get('data')
    return None