FROM python:3.10-slim

# Install ffmpeg for audio conversion
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the requested port
EXPOSE 1966

# Command to run the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:1966", "--timeout", "300", "app:app"]
