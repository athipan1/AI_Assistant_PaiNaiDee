FROM python:3.10-slim

# Set environment variables to handle SSL issues
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set C/C++ compiler environment variables for llama-cpp-python
ENV CC=gcc
ENV CXX=g++

# Install build dependencies for llama-cpp-python and OpenCV
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cmake \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project to /app
COPY . /app

# Set working directory
WORKDIR /app

# Upgrade pip and install requirements with SSL workaround
RUN pip install --upgrade pip --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

# Install requirements from the painaidee_ai_assistant directory
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r painaidee_ai_assistant/requirements.txt

# Change to the app directory where main.py is located
WORKDIR /app/painaidee_ai_assistant

# Expose port 8000 for FastAPI
EXPOSE 8000

# Run the FastAPI application
CMD ["python", "main.py"]