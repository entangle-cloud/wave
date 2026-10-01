# Build stage
FROM oven/bun:1 AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY package.json bun.lock ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy the rest of the application code
COPY . .

ARG VITE_API_ENDPOINT
ENV VITE_API_ENDPOINT=$VITE_API_ENDPOINT

RUN echo "VITE_API_ENDPOINT=$VITE_API_ENDPOINT"
RUN bun run build

# Serve stage
FROM caddy:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /srv

# Expose port 80
EXPOSE 80

# Start Caddy file server
CMD ["caddy", "file-server", "--root", "/srv", "--listen", ":80"]
