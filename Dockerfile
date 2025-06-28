# Use official Playwright Python base image
FROM mcr.microsoft.com/playwright/python:v1.51.0-noble

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy application code first (needed for Poetry to find the services package)
COPY . .

# Configure Poetry: Don't create virtual env since we're in container
RUN poetry config virtualenvs.create false

# Install dependencies using Poetry
RUN poetry install --without dev --no-interaction --no-ansi && playwright install --with-deps chromium

# Set up non-root user for security with playwright requirements
RUN groupadd -r pptruser && useradd -r -g pptruser -G audio,video pptruser \
  && mkdir -p /home/pptruser/Downloads \
  && chown -R pptruser:pptruser /home/pptruser \
  && chown -R pptruser:pptruser /app

# Run as non-root user
USER pptruser

# Add seccomp security profile for Chrome
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# set the entrypoint to include the flag
ENTRYPOINT ["python", "main.py", "--scrapers"]
# default value (can be overridden)
CMD ["1"]
