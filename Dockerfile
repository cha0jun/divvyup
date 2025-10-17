# Use the official Python 3.12 slim image as the base
FROM python:3.12-slim

# Copy the main application file into the container /app dir
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app /app
COPY cert.pem /app/cert.pem
COPY key.pem /app/key.pem

# Install FastAPI with standard dependencies, pinning the version
RUN pip install fastapi[standard]==0.117.1

# Expose port 443 for the FastAPI application
EXPOSE 443

# Set the default command to run the FastAPI app
# CMD ["fastapi", "run", "/app/main.py"]
# sudo openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443", "--ssl-keyfile", "key.pem", "--ssl-certfile", "cert.pem"]