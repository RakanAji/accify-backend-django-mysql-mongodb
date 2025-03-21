# Accify Backend

Selamat datang di proyek **Accify Backend**!  
Ini adalah backend berbasis Django untuk aplikasi mobile yang mendukung:

- **User Authentication:** Sign up, sign in, dan sign out.
- **Manajemen Kontak:** Pengguna (misalnya, pengendara) dapat menambahkan kontak terpercaya.
- **Pelacakan Real-Time:** Menyimpan dan mengambil data lokasi, kecepatan, dan kecelakaan dari perangkat IoT.
- **Notifikasi Kecelakaan:** Mengirim notifikasi real-time ke kontak dan rumah sakit.
- **Integrasi Dual Database:**  
  - **MySQL** untuk data relasional (akun, kontak, metadata perangkat IoT).  
  - **MongoDB** untuk menyimpan data time-series (lokasi dan kecepatan).

Proyek ini menggunakan Django REST Framework, djongo untuk integrasi MongoDB, dan Firebase untuk notifikasi. Terdapat juga skrip simulasi untuk meniru data perangkat IoT.

---

## Daftar Isi

- [Fitur](#fitur)
- [Prasyarat](#prasyarat)
- [Instalasi & Setup](#instalasi--setup)
- [Konfigurasi](#konfigurasi)
- [Penggunaan](#penggunaan)
  - [Menjalankan Server](#menjalankan-server)
  - [Simulasi Data IoT](#simulasi-data-iot)
- [Struktur Proyek](#struktur-proyek)
- [Kontribusi](#kontribusi)
- [Lisensi](#lisensi)

---

## Fitur

- **Manajemen Pengguna:**  
  - Sign up (username, email, password)  
  - Sign in (email, password)  
  - Sign out

- **Kontak & Pelacakan Lokasi:**  
  - Menambahkan kontak terpercaya  
  - Memperbarui dan mengambil lokasi kontak

- **Integrasi IoT:**  
  - Mendaftarkan perangkat IoT  
  - Menyimpan data lokasi dan kecepatan secara real-time ke MongoDB  
  - Deteksi kecelakaan dan pengiriman notifikasi (via Firebase dan SMS sebagai placeholder)

- **Setup Dual Database:**  
  - MySQL untuk data utama aplikasi  
  - MongoDB untuk data time-series yang cepat dan scalable

---

## Prasyarat

Pastikan sistem Anda telah menginstal hal-hal berikut sebelum menjalankan proyek ini:

1. **Python 3.8+**  
   [Download Python](https://www.python.org/downloads/)

2. **pip & virtualenv**  
   Install virtualenv (jika belum terpasang):
   ```bash
   pip install virtualenv

3. **MySQL Server**
    Instal MySQL dan buat database dengan nama accify_db.
    Buat user MySQL accify_user dengan password 1234 (atau sesuaikan di settings).

4. **MongoDB**
    Instal MongoDB dan buat database dengan nama mongoAccify_db.
    Buat user MongoDB mongoAccify_user dengan password 123 (atau sesuaikan di settings).

5. **Firebase Admin SDK Credentials**
    Tempatkan file firebase-credentials.json Anda di root proyek untuk notifikasi Firebase.

6. **Dependencies Python Lainnya:**
    Proyek ini menggunakan Django, Django REST Framework, djongo, pymysql, dan lain-lain. Semua dependency terdaftar di file requirements.txt.

## Instalasi & Setup
1. Clone Repository
    ```bash
    git clone https://github.com/your-username/crash-notifier-backend.git
    cd crash-notifier-backend

2. Buat Virtual Environment dan Aktifkan
    ```bash
    python -m virtualenv venv
    # Pada Unix/macOS:
    source venv/bin/activate
    # Pada Windows:
    venv\Scripts\activate

3. Install depedencies
    ```bash
    pip install -r requirements.txt




