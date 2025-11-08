# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Expose Cloud Run port
ENV PORT 8080
EXPOSE $PORT

# Run the app
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
