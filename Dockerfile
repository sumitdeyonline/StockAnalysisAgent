# Use lightweight Python 3.12 image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies required for vector databases (ChromaDB) and build utilities
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to explicitly cache the dependency layer
COPY requirements.txt .

# Install explicit python packages via lightning-fast uv (or pip fallback)
RUN pip install --no-cache-dir uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the entire project context into the container
COPY . .

# Expose Streamlit's default port natively required by Google Cloud Run
EXPOSE 8501

# Run the Streamlit application binding safely to all container network interfaces
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
