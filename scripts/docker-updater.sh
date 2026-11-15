#!/bin/sh
# Entry point for the `updater` service in docker-compose.yml.
#
# Every $SLURM_REFRESH_SECONDS: query Slurm on $SLURM_HOST over SSH, rebuild
# the Pelican site, and sync it into /site (a volume shared with the nginx
# `web` container). If the cluster is unreachable, the last good snapshot is
# kept and the site is still rebuilt, so the "Updated" timestamp shows how
# stale the data is.
set -u

: "${SLURM_HOST:?set SLURM_HOST (e.g. user@nillapat.coe.psu.ac.th)}"
SLURM_CLUSTER_NAME="${SLURM_CLUSTER_NAME:-Nillapat}"
SLURM_REFRESH_SECONDS="${SLURM_REFRESH_SECONDS:-300}"
SITE_DIR="${SITE_DIR:-/site}"
SNAPSHOT=content/data/cluster_status.json

# Copy the mounted key so ssh accepts its permissions regardless of the
# host file's owner/mode.
mkdir -p /root/.ssh
chmod 700 /root/.ssh
if [ -f /run/secrets/slurm_ssh_key ]; then
    cp /run/secrets/slurm_ssh_key /root/.ssh/id_slurm
    chmod 600 /root/.ssh/id_slurm
else
    echo "updater: no SSH key mounted at /run/secrets/slurm_ssh_key" >&2
fi
if [ -f /run/secrets/known_hosts ]; then
    cp /run/secrets/known_hosts /root/.ssh/known_hosts
fi
cat > /root/.ssh/config <<EOF
Host *
    IdentityFile /root/.ssh/id_slurm
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
    ServerAliveInterval 15
EOF
chmod 600 /root/.ssh/config

while true; do
    if python scripts/slurm_snapshot.py -o "$SNAPSHOT" \
        --host "$SLURM_HOST" --cluster-name "$SLURM_CLUSTER_NAME"; then
        :
    else
        echo "updater: snapshot failed; keeping previous data" >&2
    fi

    if pelican content -s publishconf.py -o /tmp/output -q; then
        # rsync replaces each file via temp-file + rename, so nginx never
        # serves a half-written page.
        rsync -a --delete-after /tmp/output/ "$SITE_DIR/"
        echo "updater: site refreshed at $(date -Iseconds)"
    else
        echo "updater: pelican build failed; site left unchanged" >&2
    fi

    sleep "$SLURM_REFRESH_SECONDS"
done
