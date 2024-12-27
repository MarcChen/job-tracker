FROM selenium/standalone-chromium:latest

# Switch to root user to install Python
USER root

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Set Python3 as the default python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies with --break-system-packages flag
RUN pip install --break-system-packages -r requirements.txt

# Switch back to the seluser for running Selenium
USER seluser

CMD ["python", "main.py"]
