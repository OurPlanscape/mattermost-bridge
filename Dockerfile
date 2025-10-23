FROM ghcr.io/astral-sh/uv:latest AS builder

FROM python:3.13.9-slim-trixie
COPY --from=builder /uv /uvx /bin/

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
ENV DEBIAN_FRONTEND=noninteractive

ADD . /app
WORKDIR /app
RUN uv sync --locked --no-install-project --dev


EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0"]