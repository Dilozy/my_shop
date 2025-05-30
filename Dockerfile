FROM python:latest

WORKDIR /usr/src/app

RUN pip install --upgrade pip && \
    pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-interaction --no-ansi --no-root

COPY . .