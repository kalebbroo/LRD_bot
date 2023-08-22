# Use an official Python runtime as the parent image
FROM python:3.11.4-alpine3.18

# Set the working directory in the container
WORKDIR /app

# Define a volume for the database
VOLUME /app/database

# Copy the local package files to the container's workspace
COPY . /app/

# Install the required packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Specify the startup command to run your bot script
CMD ["python", "-u", "./lrd_bot.py"]
