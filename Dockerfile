# Use a lightweight Python 3.12 slim image as the base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (Tesseract, Poppler, etc.)
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-chi-sim poppler-utils && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application files
COPY .env .
COPY app.py .
COPY pdf_repair_service.py .

# Expose port 8501 (Streamlit default port)
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]