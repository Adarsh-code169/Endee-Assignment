FROM python:3.11-slim

# Install system dependencies for building Endee
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libssl-dev \
    libcurl4-openssl-dev \
    unzip \
    curl \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone and build Endee
# We'll use a specific commit or version for stability
RUN git clone https://github.com/EndeeLabs/endee.git /app/endee \
    && cd /app/endee \
    && mkdir build && cd build \
    && cmake -DUSE_AVX2=OFF -DCMAKE_BUILD_TYPE=Release .. \
    && make -j$(nproc)

# Copy application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure start script is executable
RUN chmod +x start.sh

# Expose ports
EXPOSE 8000 8501

# Run the startup script
CMD ["/app/start.sh"]
