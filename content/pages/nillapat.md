Title: Nillapat System
Slug: nillapat

# Nillapat System

**Hostname:** `nillapat.coe.psu.ac.th` (`172.30.81.221`)

Nillapat is a small GPU cluster scheduled with Slurm. It has three GPU nodes,
each in its own partition: two NVIDIA nodes (CUDA) and one AMD node (ROCm).

```bash
ssh <username>@nillapat.coe.psu.ac.th
```

## Partitions and Nodes

| Partition                    | Node                      | CPUs (S:C:T) | Memory    | GPUs                          | GRES                          |
|------------------------------|---------------------------|--------------|-----------|-------------------------------|-------------------------------|
| `nvidia-rtx2080` *(default)* | `nillapat-nvidia-rtx2080` | 40 (2:10:2)  | 90,000 MB | 4 × NVIDIA GeForce RTX 2080 Ti (11 GB) | `gpu:nvidia:4`         |
| `nvidia-gtx1080`             | `nillapat-nvidia-gtx1080` | 36 (1:18:2)  | 31,000 MB | 2 × NVIDIA GeForce GTX 1080 Ti (11 GB) | `gpu:nvidia:2`         |
| `amd-9070xt`                 | `nillapat-amd-9070xt-01`  | 32 (1:16:2)  | 60,000 MB | 2 × AMD Radeon RX 9070 XT (16 GB)      | `gpu:radeon_rx_9070_xt:2` |

- All partitions have no time limit (`infinite`).
- If you don't specify `--partition`, jobs go to `nvidia-rtx2080`.
- The NVIDIA nodes run driver 550.163.01 (CUDA 12.4).
- `amd-smi` on the AMD node also lists the CPU's integrated graphics. Slurm
  doesn't schedule it, so only the two RX 9070 XT cards can be requested.

## Checking Cluster Status

```bash
sinfo                    # partition overview
sinfo -Nel               # per-node CPUs, memory, state
sinfo -o "%N %G"         # GPUs (GRES) per node
squeue -u $USER          # your jobs
```

To see a node's GPUs directly:

```bash
srun -p nvidia-rtx2080 nvidia-smi
srun -p nvidia-gtx1080 nvidia-smi
srun -p amd-9070xt amd-smi
```

## Interactive GPU Session

```bash
srun -p nvidia-rtx2080 --gres=gpu:nvidia:1 --cpus-per-task=8 --mem=16G --pty bash
```

## Example: NVIDIA RTX 2080 Ti Job

```bash
#!/bin/bash
#SBATCH --job-name=train-rtx2080
#SBATCH --partition=nvidia-rtx2080
#SBATCH --gres=gpu:nvidia:2
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=12:00:00

nvidia-smi
python3 train.py
```

## Example: NVIDIA GTX 1080 Ti Job

```bash
#!/bin/bash
#SBATCH --job-name=train-gtx1080
#SBATCH --partition=nvidia-gtx1080
#SBATCH --gres=gpu:nvidia:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=12:00:00

python3 train.py
```

## Example: AMD Radeon RX 9070 XT Job (ROCm)

```bash
#!/bin/bash
#SBATCH --job-name=train-rx9070xt
#SBATCH --partition=amd-9070xt
#SBATCH --gres=gpu:radeon_rx_9070_xt:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=12:00:00

amd-smi
python3 train.py
```

AMD GPUs use ROCm/HIP instead of CUDA. For PyTorch, install a ROCm build. It
still exposes the GPUs through `torch.cuda`.

## Example: CUDA Program

A vector-add kernel that runs on one NVIDIA GPU. Save it as `vector_add.cu`:

```c
#include <cstdio>
#include <cuda_runtime.h>

__global__ void vector_add(const float *a, const float *b, float *c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}

int main() {
    const int n = 1 << 24;                 // 16M elements
    size_t bytes = n * sizeof(float);

    float *a, *b, *c;
    cudaMallocManaged(&a, bytes);          // unified memory: visible to CPU and GPU
    cudaMallocManaged(&b, bytes);
    cudaMallocManaged(&c, bytes);
    for (int i = 0; i < n; i++) { a[i] = 1.0f; b[i] = 2.0f; }

    int threads = 256;
    int blocks = (n + threads - 1) / threads;
    vector_add<<<blocks, threads>>>(a, b, c, n);
    cudaDeviceSynchronize();

    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, 0);
    printf("GPU: %s\n", prop.name);
    printf("c[0] = %.1f, c[n-1] = %.1f (expected 3.0)\n", c[0], c[n - 1]);

    cudaFree(a); cudaFree(b); cudaFree(c);
    return 0;
}
```

Job script `cuda_job.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=cuda-vecadd
#SBATCH --partition=nvidia-rtx2080
#SBATCH --gres=gpu:nvidia:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=cuda-%j.out

# sm_75 = RTX 2080 Ti; use -arch=sm_61 on the nvidia-gtx1080 partition
nvcc -O2 -arch=sm_75 vector_add.cu -o vector_add
./vector_add
```

```bash
sbatch cuda_job.sh
cat cuda-<jobid>.out
```

## Example: MPI Program

Estimates π by numerical integration, splitting the work across MPI ranks.
Save it as `mpi_pi.c`:

```c
#include <mpi.h>
#include <stdio.h>

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    char host[MPI_MAX_PROCESSOR_NAME];
    int len;
    MPI_Get_processor_name(host, &len);
    printf("Rank %d of %d on %s\n", rank, size, host);

    const long n = 1000000000;             // number of intervals
    const double h = 1.0 / n;
    double local = 0.0;
    for (long i = rank; i < n; i += size) {
        double x = h * (i + 0.5);
        local += 4.0 / (1.0 + x * x);
    }
    local *= h;

    double pi = 0.0;
    MPI_Reduce(&local, &pi, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0) printf("pi ~= %.12f\n", pi);

    MPI_Finalize();
    return 0;
}
```

Job script `mpi_job.sh`. Each partition has one node, so the ranks run on
that node's cores:

```bash
#!/bin/bash
#SBATCH --job-name=mpi-pi
#SBATCH --partition=nvidia-rtx2080
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=mpi-%j.out

mpicc -O2 mpi_pi.c -o mpi_pi
srun ./mpi_pi                # or: mpirun -np $SLURM_NTASKS ./mpi_pi
```

## Example: MPI + CUDA (one rank per GPU)

Runs 4 MPI ranks on the RTX 2080 Ti node, each using its own GPU. Save it as
`mpi_cuda.cu`:

```c
#include <mpi.h>
#include <cstdio>
#include <cuda_runtime.h>

__global__ void fill(float *x, int n, float v) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) x[i] = v;
}

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int ngpu;
    cudaGetDeviceCount(&ngpu);
    cudaSetDevice(rank % ngpu);            // bind each rank to one GPU

    const int n = 1 << 20;
    float *d;
    cudaMalloc(&d, n * sizeof(float));
    fill<<<(n + 255) / 256, 256>>>(d, n, (float)rank);

    float first;
    cudaMemcpy(&first, d, sizeof(float), cudaMemcpyDeviceToHost);

    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, rank % ngpu);
    printf("Rank %d/%d -> GPU %d (%s), value %.0f\n",
           rank, size, rank % ngpu, prop.name, first);

    float sum = 0.0f;
    MPI_Reduce(&first, &sum, 1, MPI_FLOAT, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0) printf("Sum of ranks = %.0f\n", sum);

    cudaFree(d);
    MPI_Finalize();
    return 0;
}
```

Job script `mpi_cuda_job.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=mpi-cuda
#SBATCH --partition=nvidia-rtx2080
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --gres=gpu:nvidia:4
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:10:00
#SBATCH --output=mpi-cuda-%j.out

# Compile with nvcc, using the MPI wrapper's include/link flags
nvcc -O2 -arch=sm_75 mpi_cuda.cu -o mpi_cuda $(mpicc --showme:compile) $(mpicc --showme:link)
srun ./mpi_cuda
```

`mpicc --showme` is Open MPI syntax. With MPICH, use `mpicc -show` and pass
its include and library flags to `nvcc` yourself.

## Tips

- Request only the GPUs you need: `--gres=gpu:<type>:<count>`, up to 4 on
  `nvidia-rtx2080` and 2 on the other partitions.
- Keep `--mem` below the node limit (90,000 / 31,000 / 60,000 MB), or the job
  will stay pending.
- Always set `--time`. Partitions have no limit, but a realistic time helps
  other users plan around your job.
