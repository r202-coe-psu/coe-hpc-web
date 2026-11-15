#!/usr/bin/env python3
"""
slurm_snapshot.py

Polls Slurm (via `scontrol show nodes --json` and `squeue --json`,
Slurm >= 21.08) and writes a normalized JSON snapshot that the
`slurm_status` Pelican plugin reads at *build* time.

Run it either on a Slurm login node, or from anywhere with key-based SSH
access to one using --host, e.g.:

    python scripts/slurm_snapshot.py --host nillapat.coe.psu.ac.th

Run this on a timer (cron or systemd timer, see README.md) and rebuild the
static site after each run, e.g.:

    */5 * * * * /path/to/.venv/bin/python /path/to/scripts/slurm_snapshot.py \
        && /path/to/.venv/bin/pelican /path/to/content -o /path/to/output \
           -s /path/to/publishconf.py

The script never modifies the cluster; it only shells out to read-only
Slurm query commands. It writes atomically (tmp file + rename) so a
concurrent Pelican build never sees a half-written file.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import shlex
import tempfile
from collections import defaultdict
from datetime import datetime, timezone


def run_json(cmd: list[str], host: str | None = None) -> dict:
    if host:
        # BatchMode: never prompt for a password -- fail fast under cron.
        cmd = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=10",
            host,
            shlex.join(cmd),
        ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {out.stderr.strip()}")
    return json.loads(out.stdout)


def node_alloc_state(node: dict) -> str:
    """Collapse Slurm's verbose per-node state flags into idle/mixed/alloc/down."""
    states = {s.lower() for s in node.get("state", [])} if isinstance(
        node.get("state"), list
    ) else {str(node.get("state", "")).lower()}
    if states & {"down", "drain", "draining", "fail", "failing", "maint", "not_responding"}:
        return "down"
    if states & {"allocated", "alloc", "completing"}:
        return "alloc"
    if states & {"mixed"}:
        return "mixed"
    return "idle"


def gres_count(gres: str) -> int:
    """Sum GPU counts in a GRES string like "gpu:nvidia:4" or
    "gpu:nvidia:2(IDX:0-1),gpu:a100:1(IDX:2)"."""
    total = 0
    for item in (gres or "").split(","):
        item = item.split("(")[0].strip()
        if not item.startswith("gpu"):
            continue
        try:
            total += int(item.split(":")[-1])
        except ValueError:
            pass
    return total


def build_snapshot(nodes_json: dict, squeue: dict, cluster_name: str) -> dict:
    nodes_raw = nodes_json.get("nodes", [])
    jobs_raw = squeue.get("jobs", [])

    nodes = []
    partitions = defaultdict(
        lambda: {
            "total_nodes": 0,
            "idle_nodes": 0,
            "mixed_nodes": 0,
            "alloc_nodes": 0,
            "down_nodes": 0,
            "total_cpus": 0,
            "alloc_cpus": 0,
        }
    )

    summary = {
        "total_nodes": 0,
        "idle_nodes": 0,
        "mixed_nodes": 0,
        "alloc_nodes": 0,
        "down_nodes": 0,
        "total_cpus": 0,
        "alloc_cpus": 0,
        "total_gpus": 0,
        "alloc_gpus": 0,
        "jobs_running": 0,
        "jobs_pending": 0,
    }

    for n in nodes_raw:
        state = node_alloc_state(n)
        cpus = int(n.get("cpus", 0) or 0)
        cpus_alloc = int(n.get("alloc_cpus", n.get("alloc_cpu", 0)) or 0)
        gres = n.get("gres", "") or "-"
        partition_names = n.get("partitions", []) or ["(none)"]

        nodes.append(
            {
                "name": n.get("name"),
                "partition": partition_names[0],
                "state": state,
                "cpus": cpus,
                "cpus_alloc": cpus_alloc,
                "gres": gres,
            }
        )

        summary["total_nodes"] += 1
        summary[f"{state}_nodes"] = summary.get(f"{state}_nodes", 0) + 1
        summary["total_cpus"] += cpus
        summary["alloc_cpus"] += cpus_alloc
        summary["total_gpus"] += gres_count(gres)
        summary["alloc_gpus"] += gres_count(n.get("gres_used", ""))

        for pname in partition_names:
            p = partitions[pname]
            p["total_nodes"] += 1
            p[f"{state}_nodes"] = p.get(f"{state}_nodes", 0) + 1
            p["total_cpus"] += cpus
            p["alloc_cpus"] += cpus_alloc

    queue = []
    for j in jobs_raw:
        state = (j.get("job_state") or [""])[0] if isinstance(
            j.get("job_state"), list
        ) else str(j.get("job_state", ""))
        if state == "RUNNING":
            summary["jobs_running"] += 1
        elif state == "PENDING":
            summary["jobs_pending"] += 1

        run_time = j.get("run_time", {})
        seconds = run_time.get("number", 0) if isinstance(run_time, dict) else 0
        hh, rem = divmod(int(seconds), 3600)
        mm, ss = divmod(rem, 60)
        time_str = f"{hh:02d}:{mm:02d}:{ss:02d}" if state == "RUNNING" else "0:00"

        queue.append(
            {
                "job_id": str(j.get("job_id", "")),
                "user": j.get("user_name", "?"),
                "partition": j.get("partition", "?"),
                "name": j.get("name", "?"),
                "state": state,
                "nodes": j.get("node_count", {}).get("number", 0)
                if isinstance(j.get("node_count"), dict)
                else j.get("node_count", 0),
                "time": time_str,
            }
        )

    # Most recently submitted / currently running first, cap list length.
    queue.sort(key=lambda q: (q["state"] != "RUNNING", q["job_id"]))
    queue = queue[:50]

    partitions_out = [
        {"name": name, "state": "up", **stats} for name, stats in sorted(partitions.items())
    ]

    return {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "cluster_name": cluster_name,
        "summary": summary,
        "partitions": partitions_out,
        "nodes": nodes,
        "queue": queue,
    }


def write_atomic(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=os.path.dirname(path) or ".", prefix=".cluster_status.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        shutil.move(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        default="content/data/cluster_status.json",
        help="Where to write the JSON snapshot (default: %(default)s)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("SLURM_SSH_HOST") or None,
        help="Run the Slurm commands on this host over SSH (key auth required), "
        "e.g. nillapat.coe.psu.ac.th or user@host. Defaults to $SLURM_SSH_HOST; "
        "if unset, runs them locally.",
    )
    parser.add_argument(
        "--cluster-name",
        default=os.environ.get("SLURM_CLUSTER_DISPLAY_NAME", "CoE HPC"),
        help="Display name stored in the snapshot (default: %(default)s)",
    )
    args = parser.parse_args()

    try:
        # scontrol (unlike `sinfo --json` on Slurm >= 23.x) returns one entry
        # per node with cpus/alloc_cpus/gres/gres_used/partitions.
        nodes_json = run_json(["scontrol", "show", "nodes", "--json"], args.host)
        squeue = run_json(["squeue", "--json"], args.host)
    except (RuntimeError, FileNotFoundError, subprocess.TimeoutExpired,
            json.JSONDecodeError) as exc:
        print(f"slurm_snapshot: failed to query Slurm: {exc}", file=sys.stderr)
        return 1

    snapshot = build_snapshot(nodes_json, squeue, args.cluster_name)
    write_atomic(args.output, snapshot)
    print(f"slurm_snapshot: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
