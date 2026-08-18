FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Generate dataset if missing
RUN python generate_crisis_data.py

EXPOSE 8000

CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000", "--no-browser"]
