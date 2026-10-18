# Companion: classical vs quantum FWI pipeline

A snapshot of the team pipeline [`Charanjarugula/IBM_Qiskit_Hackathon`](https://github.com/Charanjarugula/IBM_Qiskit_Hackathon)
(upstream commit `121bb3a`, plus our local commit `efa99b9`; see `UPSTREAM_COMMITS.txt`) with **every run we made**.
It solves the same inversion problem four ways, so the methods can be compared like for like:

| Backend | Module | What it is |
|---|---|---|
| Classical reference | `classical/` | Exact forward model + finite-difference gradient inversion |
| Gate-model simulator | `simulator/` | Pauli-decomposed Hamiltonian → Trotter circuit → interferometer readout on Aer (ideal or depolarizing noise) |
| IBM hardware | `ibm_hardware/` | Same circuits through IBM Runtime with budget limits (`limits.json`) and full artifacts |
| Stride baseline | `classical/stride_baseline.py` | The paper group's own FWI software (Devito), as the external benchmark |

Every run writes `config.json`, `execution_options.json`, `manifest.json` (SHA-256 of every source file and package
versions), a `source/` snapshot, and where applicable `history.json`, `reconstruction.json`, per-circuit
`counts_*.json`, and `completed.json` or `failure.json`.

## Results in `runs/`

| Run | Status | Result |
|---|---|---|
| `small_1d` obs / classical / aer_ideal / aer_noisy | ✅ complete (88 circuits each) | truth [1.00, 1.10] → classical [0.992, 1.045], ideal [0.999, 1.045], noisy [0.995, 0.964] |
| `pulse_1d` obs / classical / aer_ideal / aer_noisy | ✅ complete (176 circuits each) | truth [1.00, 1.10] → classical [0.998, 1.015], ideal [1.000, 1.001], noisy [1.000, 0.979] |
| `matched_2d` obs / classical | ✅ complete | truth [1.03, 1.12, 1.03, 1.03] → classical [1.030, 1.031, 1.030, 1.030] after 6 iterations |
| `matched_2d` aer_ideal | ⏹ stopped | 2.5–7.6 M gates per circuit; needs `--max-gates 10000000` and a cluster |
| `stride_2d` forward | ✅ complete | Stride reference data |
| `stride_2d` invert | ⚠️ stopped at iteration 10/24 | loss diverged (0.30 → ~1,100 → 456): step size too large, **don't use** |
| `stride_3d` forward | ⏹ stopped at start | needs HPC |

`pilot_main/runs/` is the team's pilot command list run unchanged on a fresh clone of `main` (exit 0):

| Method | Relative L2 error | Time / forward |
|---|---|---|
| Classical exact | ~1e-16 | 0.002 s |
| Gate circuit, ideal | **0.58%** | 0.12 s |
| SQA (simulated quantum annealing) | 1.55% | 1.89 s |
| SA (classical annealing) | 1.58% | 0.19 s |
| Gate circuit, 0.1% depolarizing | 8.85% | 0.17 s |

Logs: `runs_*.log` (drivers), `runs/pilot_run.log` (pilot console).

## Our change: ~150× faster noisy simulation, identical output

`simulator/forward.py` (commit `efa99b9`):
1. **Noisy runs use `method='density_matrix'`.** Aer's noisy statevector re-simulates every shot; at ≤ 9 qubits the exact density matrix is far cheaper. Ideal runs are unchanged.
2. **Circuits in one forward call run in a `ProcessPoolExecutor`** (`QWAVE_WORKERS`, default = CPU count). They're built inside the workers, because multi-million-gate circuits are too big to pickle. Seeds are fixed per circuit, so results don't depend on order.

Verified: `small_1d` and `pulse_1d` reconstructions are **bit-identical** to serial runs. Density matrix vs the original
noisy statevector on 40 matched circuits: z-score mean 0.27, SD 0.87 (agreement within shot noise).
`small_1d` noisy: **~55 min → 21 s**.

## Run it

```bash
python -m venv .venv && .venv/bin/pip install -r classical/requirements.txt -r simulator/requirements.txt
C=classical/configs/small_1d.json; R=runs/small_1d
.venv/bin/python -m classical.make_observations --config $C --output $R/obs --execute
.venv/bin/python -m classical.run   --config $C --observations $R/obs/observations.npz --output $R/classical --execute
.venv/bin/python -m simulator.run   --config $C --observations $R/obs/observations.npz --output $R/aer_ideal --execute
.venv/bin/python -m simulator.run   --config $C --observations $R/obs/observations.npz --output $R/aer_noisy --execute --noise-probability 0.001
```

**Stride** needs Python 3.10 (its C extension won't build on 3.13). On macOS it also needs
`DEVITO_ARCH=gcc-15 DEVITO_LANGUAGE=openmp SDKROOT=$(xcrun --show-sdk-path)`, because Apple clang has no OpenMP.

**Cluster:** `hpc/setup.sh`, `hpc/pipeline.sh` and `hpc/job.sbatch` (64 CPUs, 128 GB) run the full pipeline,
including `matched_2d` gate simulation and Stride 3D:
`CONFIGS=matched_2d STRIDE_DIMS=3 sbatch --export=ALL hpc/job.sbatch`.

`gitignore.upstream` is the upstream `.gitignore`, renamed so the run outputs could be included here.
