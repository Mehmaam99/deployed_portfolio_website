# Use Python 3.11
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

# We set the working directory directly to /app
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from the backend folder into the current discovery path
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the CONTENTS of the backend folder into the /app directory
# This ensures app.py, scraper.py, etc. are all at the root level of /app
COPY backend/ .

# Create and set permissions for storage folders
RUN mkdir -p chroma_db scraped_pages logs && \
    chmod -R 777 chroma_db scraped_pages logs

# Set up non-root user (Hugging Face Requirement)
RUN useradd -m -u 1000 user && \
    chown -R user:user /app
USER user

# Set up user home and path
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose the default HF port
EXPOSE 7860

# We run 'app:app' because we copied the backend contents to /app root
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
