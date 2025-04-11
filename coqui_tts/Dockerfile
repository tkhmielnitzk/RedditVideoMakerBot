FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# Install Coqui TTS
RUN pip install TTS fastapi uvicorn pydub

# Create app directory
WORKDIR /app

# Copy app
COPY app /app

# Default run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
