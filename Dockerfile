FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

LABEL org.opencontainers.image.source="https://github.com/watchtowr/watchtowr-mcp"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN git clone https://github.com/watchtowr/watchtowr-api-sdk/
RUN uv sync && uv pip install -e watchtowr-api-sdk

COPY watchtowr_mcp_server/ watchtowr_mcp_server/
RUN uv pip install -e .

ENV PORT=8080
EXPOSE $PORT

CMD ["uv", "run", "watchtowr-mcp"]
