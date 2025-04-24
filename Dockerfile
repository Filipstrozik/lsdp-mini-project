FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .
    
# Create non-root user for security
RUN useradd -m scraper
RUN chown -R scraper:scraper /app
USER scraper

# Set Python path
ENV PYTHONPATH=/app

# Copy the application code
COPY scraper /app/scraper/

# Set the entry point
CMD ["python", "-m", "scraper.main"]