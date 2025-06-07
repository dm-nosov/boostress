# Base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN groupadd -r django && useradd -r -g django django

RUN apt-get update && apt-get install -y gcc \
       && apt-get install -y libpcre3 libpcre3-dev netcat-openbsd \
       && apt-get clean

# Set work directory
WORKDIR /app

# Change ownership of the app folder

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project files
COPY . /app/


RUN pip install gunicorn

# Prepare the scripts on run
RUN find /app/conf -name "*.sh" -type f -exec chmod +x {} +
RUN find /app/logs -name "*.log" -type f -exec chmod +rw {} +


RUN chown -R django:django /app

# Switch to non-root user
USER django

# Expose port 8000
EXPOSE 8000

# Start migrations and start Django (Gunicorn) server
CMD ["/app/conf/django_launch/launch_tasks.sh"]