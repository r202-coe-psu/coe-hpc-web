Title: Documentation
Slug: documentation

## Partitions

| Partition | Purpose                        | Max walltime |
|-----------|---------------------------------|--------------|
| `compute` | General-purpose CPU jobs         | 48h          |
| `gpu`     | A100 GPU jobs                    | 24h          |
| `bigmem`  | High-memory (≥512GB) jobs        | 72h          |

Live node/partition occupancy is shown on the [homepage](/) and is refreshed
automatically from Slurm every few minutes.

## SSH Access

We require SSH key authentication:

```bash
ssh-keygen -t ed25519 -C "you@example.ac.th"
ssh-copy-id <username>@hpc.coe.example.ac.th
```

## Modules

Software is provided via environment modules.

```bash
module avail            # list all available software
module load gcc/13.2
module load python/3.11
module spider pytorch   # search for a specific package
```

## Storage

| Path            | Quota   | Backed up | Purged              |
|------------------|---------|-----------|----------------------|
| `$HOME`          | 50 GB   | Yes       | Never                |
| `/scratch/$USER` | 2 TB    | No        | Files older than 30d |

## Common Slurm Commands

```bash
sbatch job.sh            # submit a job
squeue -u $USER          # view your jobs
scancel <jobid>          # cancel a job
sinfo                    # view partition/node status
sacct -j <jobid>         # job accounting / exit codes
```

## Example: GPU Job

```bash
#!/bin/bash
#SBATCH --job-name=gpu-train
#SBATCH --partition=gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00

module load cuda/12.4 python/3.11
python3 train.py
```

Questions not covered here? See [Contact](/contact/).
