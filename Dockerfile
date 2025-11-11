FROM python:3.10-slim AS builder

WORKDIR /opt/logforge

ENV PIP_NO_CACHE_DIR=1 \
    PATH="/opt/logforge/.venv/bin:${PATH}"

# Install build dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m venv .venv \
    && .venv/bin/pip install --upgrade pip \
    && .venv/bin/pip install ".[dev]"

# ------------------------------------------------------------------------

FROM python:3.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOGFORGE_STATE_DIR=/data/logforge \
    LOGFORGE_CONFIG=/data/logforge/config.yaml \
    PATH="/opt/logforge/.venv/bin:${PATH}"

WORKDIR /opt/logforge

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --system --group --home /opt/logforge logforge

COPY --from=builder /opt/logforge /opt/logforge

RUN chown -R logforge:logforge /opt/logforge

USER logforge

VOLUME ["/data/logforge"]

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD curl -f http://localhost:8080/api/health || exit 1

ENTRYPOINT ["python", "-m", "logforge", "api", "serve", "--host", "0.0.0.0"]

