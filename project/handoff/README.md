# Aperion handoff (18 Oct 2026, ~01:40)

## 1. `1_pilot/pilot_results.tar.gz`
The team's pilot command list, run unchanged on a fresh clone of `Charanjarugula/IBM_Qiskit_Hackathon` `main` with Python 3.12. Exit 0. The tarball holds the whole `runs/` folder plus `runs/pilot_run.log` (the full console output). The final `tar` was re-run once, only to add that log.

## 2. `2_reconstructions/reconstruction_runs.tar.gz`
The `runs/` folder from `IBM_Qiskit_Hackathon` at base commit `121bb3a` (see `4_code_changes/base_commit.txt`), plus every driver log (`runs_*.log`). Each run directory contains `config.json`, `execution_options.json`, `comparison.json`, `manifest.json` (source SHA-256 hashes and package versions), a `source/` snapshot, and, where they apply, `history.json`, `reconstruction.json`, per-circuit `counts_*.json`, and `completed.json` or `failure.json`.

| Run | Circuits | Status |
|---|---|---|
| small_1d obs / classical | n/a | complete |
| small_1d aer_ideal | 88 | complete |
| small_1d aer_noisy (p=0.001) | 88 | complete (density_matrix + parallel code; see 4) |
| pulse_1d obs / classical | n/a | complete |
| pulse_1d aer_ideal / aer_noisy | 176 / 176 | complete (density_matrix + parallel code) |
| matched_2d obs / classical | n/a | complete |
| matched_2d aer_ideal | 0 | stopped on request before the first forward call finished. 2.5–7.6M gates per circuit; needs `--max-gates 10000000` |
| stride_2d forward | n/a | complete |
| stride_2d invert | n/a | stopped on request at iteration 10 of 24 (`failure.json` = SystemExit from the kill). Vp models for iterations 1–10 are saved as `.h5`. The loss diverged (0.30 → ~1,100 → 456), so don't use these. |
| stride_3d forward | n/a | stopped on request just after starting (SystemExit) |

Stride environment: Python 3.10 via uv (Stride's C extension won't build on 3.13), and Devito 4.8.23 with `DEVITO_ARCH=gcc-15 DEVITO_LANGUAGE=openmp SDKROOT=$(xcrun --show-sdk-path)`, because Apple clang has no OpenMP.

## 3. `3_ibm_job/`: original IBM job
- **Job `db9smd9gv2cc73e60pm0`** on **`ibm_marrakesh`**, Open plan, SamplerV2 in Batch mode, 4,000 shots per circuit, DD and twirling on
- **Measured QPU usage: 9 s** (`qpu_charge_time_seconds`); circuit execution 6.62 s; created 19:23:33Z, running 19:23:35Z, finished 19:23:53Z
- `raw_counts.json`: full bitstring counts for all 6 PUBs, fetched from IBM just now. Each PUB is labelled with bleed/steps/fold.
- `job_metadata.json`: status, timestamps, usage, metrics, result metadata
- `analysed_results_pub_order.json`: raw/post-selected values and SEs, in PUB order
- `submit_script.py`: the exact script that submitted the job (it reproduces notebook 03's `RUN_ON_IBM` cell; it reads the API key at run time and never stores it)
- `hw_run.log`, `hardware_fake_kingston_DRYRUN.json`, `03_noise_results.json`: the submission log, the free dry run and the noise-model reference

## 4. `4_code_changes/`
- `simulator_forward.diff`: the only change to repo code (`simulator/forward.py`, not committed):
  1. Noisy runs use `method='density_matrix'` instead of `statevector`. Noiseless runs are unchanged.
  2. Circuits within one forward call are built, transpiled and simulated in a `ProcessPoolExecutor` (`QWAVE_WORKERS` env var, default = CPU count). Per-circuit seeds are unchanged, so the output matches the serial run exactly.
  - Verified: `small_1d` and `pulse_1d` noisy and ideal reconstructions are **bit-identical** to serial runs of the same method. Density matrix vs the original noisy statevector on 40 matched circuits: z-score mean 0.27, SD 0.87, so they agree within shot noise. Speed: `small_1d` noisy went from about 55 min to 21 s.
  - The `small_1d` and `pulse_1d` aer_noisy results in section 2 come from this modified code (the manifests carry the modified source hash).
- `run_all.sh`, `run_stride.sh`: the local driver scripts
- `hpc_scripts/`: `setup.sh`, `pipeline.sh`, `job.sbatch` for FAU Athene. Not used, because Athene needs FAU's OpenVPN plus MFA.

**Overnight runs still running: none.** Everything was stopped on request at about 01:00. Nothing will write further output. No HPC jobs were submitted.
