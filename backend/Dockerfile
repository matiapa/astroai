FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (if any needed for opencv or other libs, often 'ffmpeg', 'libsm6', 'libxext6' for opencv)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["python", "src/api/server.py"]
