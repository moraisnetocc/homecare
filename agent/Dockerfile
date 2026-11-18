FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir .
RUN useradd --system --uid 10001 agent && mkdir -p /data && chown agent:agent /data
USER agent
ENV HOMECORE_AGENT_DB=/data/agent.sqlite3 HOMECORE_AGENT_HOST=0.0.0.0 HOMECORE_AGENT_PORT=8081
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/health', timeout=3)"
CMD ["python", "-m", "homecore_agent"]
