FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY alembic ./alembic

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "app.runtime"]
