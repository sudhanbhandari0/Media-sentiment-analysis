FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

# COPY the processor/requirements.txt from context into the image
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy the consumer script
COPY consumer.py .

CMD ["python", "consumer.py"]

