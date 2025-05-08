# FROM python:3.10-slim
FROM --platform=linux/amd64 python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg git g++ && rm -rf /var/lib/apt/lists/*

# Install Coqui TTS
RUN pip install --upgrade pip setuptools wheel
RUN pip install fastapi 
RUN pip install uvicorn 
RUN pip install pydub
RUN pip install TTS 


# Create app directory
WORKDIR /app

# Copy app
COPY app /app

# Default run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]