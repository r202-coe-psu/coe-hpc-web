# syntax=docker/dockerfile:1

# --- Build stage: compile Tailwind/DaisyUI CSS and render the static site ---
FROM node:20-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv pipx \
    && rm -rf /var/lib/apt/lists/* \
    && pipx install poetry \
    && pipx ensurepath

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true \
    && poetry install --no-root --only main

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Live Slurm data is never baked into the image; the sample snapshot keeps
# the build hermetic. Mount a real cluster_status.json at runtime (or rebuild
# the image) to publish live data instead -- see README.md.
RUN npm run css:build \
    && poetry run pelican content -o output -s publishconf.py

# --- Runtime stage: serve the prerendered static site ---
FROM nginx:1.27-alpine AS runtime

COPY --from=builder /app/output /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
