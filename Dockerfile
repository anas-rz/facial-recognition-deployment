# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV APP_HOME /app
ENV PORT 8000

# Set the working directory in the container
WORKDIR $APP_HOME

# Copy the current directory contents into the container at /app
COPY . $APP_HOME

# Install dependencies
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install tf-keras

# Expose the port the app runs on
EXPOSE $PORT

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

