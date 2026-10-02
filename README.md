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

Requires Python 3.10+ and Node 18+.

```bash
make install       # creates .venv, installs Pelican + npm deps
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

On a host with Slurm client tools and access to this repo (typically the
login/management node, or anywhere that can run `sinfo`/`squeue`), set up a
cron job or systemd timer that regenerates the snapshot and rebuilds:

```cron
*/5 * * * * cd /path/to/hpc-web && .venv/bin/python scripts/slurm_snapshot.py \
    && .venv/bin/pelican content -o output -s publishconf.py >> /var/log/hpc-web.log 2>&1
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
