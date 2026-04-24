# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set the working directory in the container to /app
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .

# Install dependencies, specifically using CPU version of PyTorch to save huge amount of space
# By default, pip might pull the GPU version which is over 2GB
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy the rest of the working directory contents to /app
COPY . ./

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
