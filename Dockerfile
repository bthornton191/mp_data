# Use an official Python runtime as a parent image
FROM python:3.10.5-slim-buster

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Make port 80 available to the world outside this container
# Run app.py when the container launches
CMD gunicorn -b 0.0.0.0:8080 app:SERVER
