Title: Getting Started
Slug: getting-started

# Requesting an Account

Accounts on the CoE HPC cluster are available to College of Engineering faculty,
staff, and their students/collaborators.

1. Ask your supervisor (PI) to email **hpc-support@coe.example.ac.th** with your
   full name, university ID, and department.
2. You will receive your username and SSH setup instructions within 2 business
   days.
3. Set up [multi-factor / SSH key authentication](/documentation/#ssh-access)
   before your first login.

## Logging In

```bash
ssh <username>@hpc.coe.example.ac.th
```

## Your First Job

Jobs are scheduled with **Slurm**. A minimal batch script:

```bash
#!/bin/bash
#SBATCH --job-name=hello-hpc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=00:10:00
#SBATCH --output=hello-%j.out

module load python/3.11
python3 -c "print('Hello from the CoE HPC cluster!')"
```

Submit it with:

```bash
sbatch hello.sh
squeue -u $USER
```

See the [Documentation](/documentation/) page for partitions, modules, and
storage quotas, or the homepage for live cluster status.
