# Stage 1: Build and test
FROM python:3.8-slim as builder

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Install testing packages (pytest, coverage, etc.)
RUN pip install pytest coverage

# Run unit tests
RUN pytest tests/

# Stage 2: Production image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Copy the application code from the builder stage
COPY --from=builder /app /app

# Make port 5000 available for Flask
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "app.py"]
#automated testing implemented