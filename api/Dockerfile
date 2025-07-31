# Use official slim Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

#Install system deps (if needed for any libraries)
RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker layer caching 
COPY api/requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy application code
COPY api ./api

# 5. Set environment variables (optional)
# ENV REDIS_HOST=redis
# ENV MONGO_URI=mongodb://mongo:27017/myLearningDB

#Expose FastAPI default port
EXPOSE 8000

#Launch the app with Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]