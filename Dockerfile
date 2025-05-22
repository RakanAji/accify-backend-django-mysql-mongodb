# Gunakan Python 3.10 slim
FROM python:3.10-slim

# Install deps untuk mysqlclient dan building
RUN apt update && apt install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Atur direktori kerja
WORKDIR /app

# Salin semua file terlebih dahulu, termasuk requirements.txt
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port Django
EXPOSE 8000