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

RUN pip install uwsgi

# Prepare the migration script on run
RUN chmod +x /app/conf/django_launch/launch_tasks.sh

RUN chown -R django:django /app

# Switch to non-root user
USER django

RUN python manage.py collectstatic --noinput

# Configure uWSGI
COPY conf/uwsgi/uwsgi.ini /app/

# Expose port 8000
EXPOSE 8000

# Start migrations and uWSGI server
CMD ["/app/conf/django_launch/launch_tasks.sh"]