FROM python:3.11-slim-bullseye as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


FROM python:3.11-slim-bullseye

RUN mkdir -p /app

WORKDIR /app

COPY --from=requirements-stage /tmp/requirements.txt /

RUN pip install --no-cache-dir --upgrade -r /requirements.txt

COPY ./app /app/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
