Title: Getting Started
Slug: getting-started

# Requesting an Account

Accounts on the CoE HPC cluster are available to Department of Computer Engineering, Faculty of Engineering, Prince of Songkla University staff, and their students/collaborators.

1. Go to http://nillapat.coe.psu.ac.th, login with PSU Passport, the account will automaticly create, allow only PSU intranet and outsite PSU using VPN.
2. It you would like to login via ssh the username is s<student_id> and password is CoE-<student_id> please change the password at the first time login.


## Logging In

```bash
ssh s<username>@nillapat.coe.psu.ac.th
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
