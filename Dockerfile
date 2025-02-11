FROM selenium/standalone-chromium:132.0

USER root

WORKDIR /app

# RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    mv ~/.local/bin/poetry /usr/local/bin/poetry

COPY pyproject.toml /app/

COPY src/ /app/src/

COPY main.py /app/

RUN poetry install --only main

USER seluser

CMD ["poetry", "run", "python", "/app/main.py"]
