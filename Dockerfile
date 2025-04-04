FROM python:3.10.14-slim

# Install system dependencies
RUN apt update && apt-get install -y \
    ffmpeg \
    espeak-ng \
    python3-pip \
    wget \
    curl \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libfontconfig1 \
    libxss1 \
    libxtst6 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libx11-xcb1 \
    libxext6 \
    libx11-6 \
    libgtk-3-0 \
    && apt clean

RUN apt update
RUN apt-get install -y ffmpeg
RUN apt install python3-pip -y

# Create application directory
RUN mkdir /app
ADD . /app
WORKDIR /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Install Playwright browser 
RUN playwright install --with-deps

# Run the application
# CMD ["python3", "main.py"]
# commande to run the app but nothing else
CMD ["tail", "-f", "/dev/null"]
