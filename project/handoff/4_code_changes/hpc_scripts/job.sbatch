#!/bin/bash
#SBATCH --job-name=qwave
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=128G
#SBATCH --time=7-00:00:00
#SBATCH --output=runs/slurm-%j.log
# ponytail: partition left to the cluster default; add #SBATCH --partition=... if Athene requires one.
# Submit from repo root: CONFIGS=matched_2d STRIDE_DIMS=3 sbatch --export=ALL hpc/job.sbatch
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
bash hpc/pipeline.sh
