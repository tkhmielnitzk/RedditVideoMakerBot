# FROM python:3.9

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# CMD ["python", "scripts/manager.py"]

FROM apache/airflow:2.7.0

# Install any dependencies your scripts need
RUN pip install --no-cache-dir -r requirements.txt

# Optionally copy your custom scripts into the image if needed
COPY ./scripts /opt/airflow/scripts