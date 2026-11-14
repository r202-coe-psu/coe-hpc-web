Title: Documentation
Slug: documentation

## Partitions

| Partition | Purpose                        | 
|-----------|---------------------------------|
| `compute` | General-purpose CPU jobs         |
| `gpu`     | A100 GPU jobs                    |
| `bigmem`  | High-memory (≥512GB) jobs        ||

Live node/partition occupancy is shown on the [homepage](/) and is refreshed
automatically from Slurm every few minutes.

## SSH Access

We require SSH key authentication:

```bash
ssh-keygen -t ed25519 -C "<username>@psu.ac.th"
ssh-copy-id <username>@psu.ac.th
```

<!---
## Storage

| Path            | Quota   | Backed up | Purged              |
|------------------|---------|-----------|----------------------|
| `$HOME`          | 50 GB   | Yes       | Never                |
| `/scratch/$USER` | 2 TB    | No        | Files older than 30d |
--->

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

## Example: Multi-Node MPI Job

```bash
#!/bin/bash
#SBATCH --job-name=mpi-sim
#SBATCH --partition=compute
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=16
#SBATCH --time=08:00:00

module load openmpi/4.1 gcc/13.2
srun ./simulation
```

## Example: Job Array

Submit many similar jobs (e.g. a parameter sweep) as a single array:

```bash
#!/bin/bash
#SBATCH --job-name=sweep
#SBATCH --partition=compute
#SBATCH --array=1-20
#SBATCH --time=01:00:00
#SBATCH --output=sweep-%A_%a.out

module load python/3.11
python3 run_trial.py --trial $SLURM_ARRAY_TASK_ID
```

Questions not covered here? See [Contact](/contact/).
