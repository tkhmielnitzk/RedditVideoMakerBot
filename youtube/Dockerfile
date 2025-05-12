# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the necessary files
COPY manage_videos.py . 
COPY generate_token.py .
COPY requirements.txt . 

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Keep container running in idle mode (Airflow will trigger the script)
CMD ["tail", "-f", "/dev/null"]