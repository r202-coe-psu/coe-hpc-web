# --- Stage 1: build Tailwind/daisyUI CSS ---
FROM node:20-alpine AS css-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY theme ./theme
RUN npm run css:build

# --- Stage 2: build the static site with Pelican ---
FROM python:3.14-slim AS site-builder
WORKDIR /app
RUN pip install --no-cache-dir poetry==2.3.4
ENV POETRY_VIRTUALENVS_CREATE=false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --only main
COPY pelicanconf.py publishconf.py ./
COPY content ./content
COPY plugins ./plugins
COPY theme ./theme
COPY --from=css-builder /app/theme/static/css/style.css ./theme/static/css/style.css
ARG SITEURL=""
ENV SITEURL=${SITEURL}
RUN pelican content -s publishconf.py -o output

# --- Stage 2b: periodic Slurm status updater (docker-compose `updater`) ---
# Reuses the site-builder environment, adds ssh/rsync, and rebuilds the site
# into a volume shared with nginx. Build it with `--target updater`.
FROM site-builder AS updater
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-client rsync tzdata \
    && rm -rf /var/lib/apt/lists/*
COPY scripts ./scripts
CMD ["sh", "scripts/docker-updater.sh"]

# --- Stage 3: serve the static site ---
FROM nginx:alpine
COPY --from=site-builder /app/output /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
