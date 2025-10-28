# Use official Playwright Python base image
FROM mcr.microsoft.com/playwright/python:v1.51.0-noble

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy pyproject.toml first for better caching
COPY pyproject.toml .

# Create virtual environment
RUN uv venv /opt/venv

# Set environment variables to use the virtual environment
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies from pyproject.toml
RUN uv pip install -r pyproject.toml

# Copy application code first (needed for Poetry to find the services package)
COPY . .

# Install Playwright browsers
RUN playwright install --with-deps chromium

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
