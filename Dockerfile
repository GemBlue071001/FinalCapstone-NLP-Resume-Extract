# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install dependencies and the SpaCy model in a single layer to optimize image size
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

# Create necessary directories with appropriate permissions
RUN mkdir -p /tmp/flask_sessions /app/flask_sessions /app/uploads && \
    chmod -R 777 /tmp/flask_sessions /app/flask_sessions /app/uploads

# Create the app_error.log file and set write permissions
#RUN touch /app/app_error.log && chmod 777 /app/app_error.log

# Ensure all relevant directories have the correct permissions
RUN chmod -R 777 /app

# Copy the rest of the application code to /app
COPY . /app/

# Ensure the upload directory and app directory have the correct permissions
RUN mkdir -p /app/uploads && \
    chmod -R 777 /app/uploads && \
    chmod -R 777 /app
    
# Expose the port the app runs on
EXPOSE 7860

# Set environment variables for Flask
ENV FLASK_APP=app.py \
    FLASK_ENV=production

# Command to run the application
#CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:7860", "--timeout", "120", "app:app"]
CMD ["gunicorn", "--workers=5", "--threads=2", "--bind=0.0.0.0:7860", "--timeout=120", "app:app"]