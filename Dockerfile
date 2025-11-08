# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose the Cloud Run port
EXPOSE 8080
ENV PORT 8080

# Start Uvicorn on 0.0.0.0 and port from environment variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
