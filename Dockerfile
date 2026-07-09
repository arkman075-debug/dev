# Use Python 3.9
FROM python:3.9-slim

# Install ffmpeg and clean up
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Create downloads folder
RUN mkdir -p downloads

# Start the app using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
