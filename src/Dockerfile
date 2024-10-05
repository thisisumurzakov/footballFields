# Use an official Python runtime as a parent image
FROM python:3.11.6-alpine

# Set environment variables to ensure that Python outputs are sent straight to terminal without buffering, and to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container to /usr/src/app
WORKDIR /usr/src/app

# Install system dependencies required for psycopg2 and other packages
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    python3-dev

# Create a virtual environment and add it to PATH
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install Python dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Run Django collectstatic, this step is typically for production only
RUN python manage.py collectstatic --noinput

# Expose port 8000 to allow communication to/from the server
EXPOSE 8000

# Start the main process.
CMD ["gunicorn", "--bind", "0.0.0.0:8000"]
