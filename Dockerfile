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

# Copy the src folder into the container at /app
COPY src/ /app/src/

# Set PYTHONPATH so Python can find your src folder
ENV PYTHONPATH=/app/src

# Copy main.py file 
COPY main.py /app/

# Switch back to the seluser for running Selenium
USER seluser

# Run the Python script
CMD ["python", "/app/main.py"]
