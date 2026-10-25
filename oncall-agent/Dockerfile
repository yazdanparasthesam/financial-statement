# Compose-only responder image. Docker CLI is needed solely for the exact
# `docker compose restart backend` runbook action; agent.py never invokes a shell.
FROM docker:27-cli
RUN apk add --no-cache python3 py3-yaml \
    && docker compose version
WORKDIR /app
COPY agent.py runbooks.yaml ./
EXPOSE 8090
CMD ["python3", "/app/agent.py", "--runbooks", "/app/runbooks.yaml", "--cwd", "/workspace"]
