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

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/

# Install Python dependencies with --break-system-packages flag
RUN pip install --break-system-packages -r requirements.txt

# Copy the main.py file from the src directory into the container at /app
COPY src/selenium_script.py /app/

# Switch back to the seluser for running Selenium
USER seluser

CMD ["python", "selenium_script.py"]
