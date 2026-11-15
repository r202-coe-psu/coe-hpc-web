# CoE HPC Website

A static site for a College of Engineering HPC cluster, built with
[Pelican](https://getpelican.com/) and styled with
[Tailwind CSS](https://tailwindcss.com/) + [DaisyUI](https://daisyui.com/).
The homepage shows a **live cluster status dashboard** (nodes, partitions,
GPU/CPU occupancy, job queue) sourced from Slurm.

## How the Slurm integration works

Pelican produces a static site, so there is no running backend process on the
webserver. Instead:

1. `scripts/slurm_snapshot.py` runs **on a Slurm login/management node** and
   calls `sinfo --json` / `squeue --json` (read-only). It writes a normalized
   snapshot to `content/data/cluster_status.json`.
2. The `slurm_status` Pelican plugin (`plugins/slurm_status/`) reads that
   JSON at *build* time and exposes it to every template as `SLURM_STATUS`.
3. A cron job / systemd timer re-runs the snapshot script and rebuilds the
   site every few minutes, so the "live" status is really "recently
   refreshed static HTML" — simple, fast, and has no attack surface on the
   public webserver.

If `content/data/cluster_status.json` doesn't exist yet (e.g. local
development on a laptop with no Slurm access), the plugin falls back to
`content/data/cluster_status.sample.json` and the homepage shows a "demo
data" badge.

## Project layout

```
content/
  pages/        Getting Started, Documentation, Contact
  articles/     News & announcements (dated Markdown posts)
  data/         cluster_status.json (generated, gitignored) + .sample.json
theme/
  templates/    base.html, index.html, page.html, article.html, archives.html
  static/       css/ (Tailwind input + compiled output), js/, img/
plugins/
  slurm_status/ Pelican plugin that injects SLURM_STATUS into templates
scripts/
  slurm_snapshot.py  Polls Slurm, writes content/data/cluster_status.json
pelicanconf.py / publishconf.py   Pelican settings (dev vs. production)
```

## Local development

Requires Python 3.11+, [Poetry](https://python-poetry.org/), and Node 18+.

```bash
make install       # poetry install (Pelican) + npm install (Tailwind/DaisyUI)
make devserver     # builds CSS, builds the site, serves + autoreloads at :8000
```

In a second terminal, keep Tailwind rebuilding on change:

```bash
make css-watch
```

Edit Markdown in `content/`, or templates in `theme/templates/`. Pelican's
`-r` autoreload will rebuild on save; refresh your browser.

## Customizing branding

No branding/colors are locked in yet — `theme/static/css/input.css` picks two
built-in DaisyUI themes (`corporate` for light, `business` for dark, toggled
by the button in the navbar and persisted in `localStorage`). To use your
institution's palette, either:

- swap in different built-in DaisyUI theme names, or
- define a custom DaisyUI theme block (see the [DaisyUI theming
  docs](https://daisyui.com/docs/themes/)) with your institution's exact
  colors, then reference it in `input.css`.

Also update the placeholder address in `content/pages/contact.md` and the
support email address used throughout the templates/content
(`hpc-support@coe.example.ac.th`).

## Deploying the Slurm snapshot + rebuild on a schedule

The snapshot script can query the cluster remotely over SSH, so the build
host doesn't need Slurm installed. It only needs key-based SSH access (no
password prompt) to the login node, by default `nillapat.coe.psu.ac.th`:

```bash
make slurm-snapshot                              # ssh nillapat.coe.psu.ac.th, runs scontrol/squeue
make slurm-snapshot SLURM_HOST=user@other-host   # a different login node / SSH user
make slurm-snapshot SLURM_HOST=                  # run scontrol/squeue locally instead
# or directly:
poetry run python scripts/slurm_snapshot.py --host nillapat.coe.psu.ac.th --cluster-name Nillapat
```

`make deploy` refreshes the snapshot before it rebuilds the Docker image. If
the cluster is unreachable, the build uses the previous snapshot. With Docker
Compose, the `updater` service refreshes the status on its own (see
[Automatic Slurm status updates](#automatic-slurm-status-updates)).

Without Docker, rebuild on a timer:

```cron
*/5 * * * * cd /path/to/hpc-web && poetry run python scripts/slurm_snapshot.py --host nillapat.coe.psu.ac.th \
    && poetry run pelican content -o output -s publishconf.py >> /var/log/hpc-web.log 2>&1
```

Then sync/serve `output/` with your webserver of choice (nginx, Apache, an
S3+CDN bucket, etc.) — it's plain static HTML/CSS/JS.

If the webserver and the Slurm login node are different machines, run the
snapshot script on the login node and `rsync` just
`content/data/cluster_status.json` to the build host before rebuilding.

## Production build

```bash
make publish   # uses publishconf.py — set SITEURL there first
```

## Docker deployment

The `Dockerfile` is a multi-stage build: it compiles the Tailwind/DaisyUI CSS
and renders the Pelican site with `publishconf.py` in a build stage, then
serves the prerendered static output with nginx.

```bash
make docker-build   # docker build -t coe-hpc-web .
make docker-run     # docker run --rm -p 8000:80 coe-hpc-web
```

For a long-running deployment use Docker Compose (`docker-compose.yml`), which
adds a restart policy, healthcheck, read-only filesystem and log rotation:

```bash
make deploy                    # docker compose up -d --build  (serves on :8000)
HOST_PORT=80 make deploy       # serve on a different host port (or set it in .env)
make deploy-down               # docker compose down
```

### Automatic Slurm status updates

Compose runs two services that share a `site` volume:

- `web`: nginx serving the site. Its image includes a prebuilt copy, which
  fills the volume on first start.
- `updater`: every `SLURM_REFRESH_SECONDS` (default 300) it SSHes to the
  Slurm login node, runs `scontrol`/`squeue`, rebuilds the site with Pelican,
  and `rsync`s it into the volume. If the cluster is unreachable it keeps the
  last snapshot, and the "Updated" timestamp on the homepage shows its age.

The updater needs a passwordless SSH key for an account on the login node.
It mounts `~/.ssh/id_ed25519` and `~/.ssh/known_hosts` read-only and connects
as `$USER`. To change any of this, set it in `.env`:

```bash
SLURM_SSH_USER=myuser                       # login name on nillapat
SLURM_SSH_KEY=/home/me/.ssh/id_hpcweb       # key to mount (no passphrase)
SLURM_HOST_NAME=nillapat.coe.psu.ac.th
SLURM_REFRESH_SECONDS=300
TZ=Asia/Bangkok                             # timezone for the "Updated" timestamp
```

For production, use a dedicated key. On the login node, consider a
read-only account, or restrict the key in `authorized_keys`.

```bash
docker compose logs -f updater   # "updater: site refreshed at ..." every cycle
```

You can still use `make deploy` to rebuild the images after changing content,
templates or code. No cron job is needed for the status.
