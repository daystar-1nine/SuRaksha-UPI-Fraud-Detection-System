# Use python:3.11-slim as base image to keep it lightweight
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libzbar0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install python packages (with gunicorn)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the backend files
COPY . .

# Expose port (Render automatically maps this)
EXPOSE 5000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=5000
ENV FLASK_ENV=production

# Run app using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
