FROM python:3.12-slim

# Install ffmpeg for audio conversion
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 1966

# Run with gevent worker for SSE / streaming response support
CMD ["gunicorn", "--bind", "0.0.0.0:1966", "--worker-class", "gevent", "--workers", "2", "--timeout", "300", "app:app"]
