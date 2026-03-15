FROM python:3.11-slim

WORKDIR /app

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
