FROM python:3.12-slim

# Install dependencies, Supervisor, and Caddy
RUN apt-get update && apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl supervisor libpq-dev gcc && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list && \
    apt-get update && apt-get install -y caddy && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies using uv
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv pip install --system -r pyproject.toml

# Copy source code
COPY . .

# Setup Caddy and Supervisor configs
COPY Caddyfile /etc/caddy/Caddyfile
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose Caddy's port
EXPOSE 80

# Start Supervisor which runs both Uvicorn and Caddy
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]