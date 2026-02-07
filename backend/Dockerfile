FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV and other libs
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set Python path to include the app directory
ENV PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 8080

# Run the application
CMD ["python", "-m", "src.api.server"]
