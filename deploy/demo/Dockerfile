# Synthetic HITL demo image. No LLM weights. Not a production image.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CAR_PROPOSAL_HOOK=off \
    CAR_DEMO_HOST=0.0.0.0 \
    CAR_DEMO_PORT=8000 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY demo-seeds ./demo-seeds
COPY policy ./policy
COPY docs/ui/prototype ./docs/ui/prototype

RUN pip install --no-cache-dir -e ".[demo]" \
    && useradd --system --uid 10001 --home-dir /app --shell /usr/sbin/nologin car-demo \
    && chown -R car-demo:car-demo /app

USER car-demo
EXPOSE 8000

# Container must listen on 0.0.0.0; compose publishes 127.0.0.1 on the host.
CMD ["python", "-m", "controlled_agent_runtime.demo", "--host", "0.0.0.0", "--port", "8000", "--allow-public-bind"]
