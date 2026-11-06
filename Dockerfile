# Polyglot Discord Bot Dockerfile
FROM python:3.12-slim

# Prevent Python from buffering stdout/stderr and writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and assets
COPY bot/ bot/
COPY assets/ assets/
COPY main.py .

# Create directory for persistent SQLite database
RUN mkdir -p /app/data

# Declare volume mount point for database persistence
VOLUME ["/app/data"]

# Start the bot
CMD ["python", "main.py"]

