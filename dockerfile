# Use the official Python image as the base image for testing
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Expose port 5000 (for reference but not necessary for testing)
EXPOSE 5000

# This is where the testing setup differs. You can run your tests here.
# Assuming you have a "test.py" file in the same directory as your Dockerfile.
CMD ["python", "test.py"]