"""
Pelican plugin: slurm_status

Reads a JSON snapshot of the Slurm cluster state (produced out-of-band by
scripts/slurm_snapshot.py, normally via cron/systemd-timer on a login node)
and exposes it to every template as the `SLURM_STATUS` global context
variable.

This plugin never talks to Slurm itself -- Pelican builds are static, so a
separate, periodically-run script owns the privilege of shelling out to
`sinfo`/`squeue`. This keeps the site build hermetic and safe to run
anywhere (including a laptop with no Slurm installed), and keeps the
webserver host from needing Slurm client tools at all if the snapshot is
synced in from elsewhere.

If SLURM_STATUS_JSON does not exist (e.g. local development), the plugin
falls back to SLURM_STATUS_SAMPLE_JSON and marks the data as demo/sample so
templates can show a banner.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

try:
    from pelican import signals
except ImportError:  # pragma: no cover - only used for type checking outside Pelican
    signals = None


def _load_status(settings):
    live_path = settings.get("SLURM_STATUS_JSON", "content/data/cluster_status.json")
    sample_path = settings.get(
        "SLURM_STATUS_SAMPLE_JSON", "content/data/cluster_status.sample.json"
    )

    for path, is_sample in ((live_path, False), (sample_path, True)):
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("slurm_status: failed to read %s: %s", path, exc)
                continue
            data["_is_sample"] = is_sample
            data["_source_path"] = path
            return data

    logger.warning(
        "slurm_status: no cluster status JSON found (looked for %s and %s); "
        "the cluster status widget will be hidden.",
        live_path,
        sample_path,
    )
    return None


def add_slurm_status(pelican_object):
    settings = pelican_object.settings
    settings["SLURM_STATUS"] = _load_status(settings)


def register():
    if signals is not None:
        signals.initialized.connect(add_slurm_status)
