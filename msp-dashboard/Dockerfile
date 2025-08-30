# Use the official Python image as the base image
FROM python:3.11

# Set the working directory to /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV C_FORCE_ROOT=true

# Install system dependencies required for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Upgrade pip, setuptools, wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install pinned packages in one command to reduce layers
RUN pip install --no-cache-dir \
    Django==5.2.3 djangorestframework==3.15.1 django-tenants==3.8.0 \
    psycopg2==2.9.10 redis==5.2.1 django-redis==5.4.0 \
    celery==5.5.1 django-allauth==65.9.0 django-crispy-forms==2.1 \
    django-ckeditor==6.7.0 django-debug-toolbar==4.4.6 django-auditlog==3.0.0 \
    django-taggit==5.0.1 django-otp==1.6.0 django-two-factor-auth==1.17.0 \
    django-phonenumber-field==7.1.0 django-multiselectfield==0.1.12 django-recurrence==1.11.1 \
    django-timezone-field==7.1 django-role-permissions==3.1.1 django-hashid-field==3.3.7 \
    django-embed-video==1.4.8 django-extensions==3.2.1 django-formtools==2.5.1 \
    django-js-asset==2.1.0 django-mathfilters==1.0.0 django-discover-runner==1.0 \
    django-phone-field==1.8.1 django-valkey==0.1.3 django-celery-beat==2.8.1 \
    dj-database-url==2.1.0 dj-stripe==2.8.3 gunicorn==21.2.0 whitenoise==6.5.0

# Install remaining packages from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install spaCy model with retry logic
RUN python -m spacy download en_core_web_sm || \
    (sleep 10 && python -m spacy download en_core_web_sm) || \
    (echo "spaCy model download failed, but continuing...")

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p ./media/public/images/default/users/
RUN mkdir -p /var/log/django

# Default media files will be created at runtime if needed

# Expose port 8000
EXPOSE 8000

# Make build script executable
RUN chmod +x /app/build.sh

# Start the app with your build script
CMD ["bash", "build.sh"]
