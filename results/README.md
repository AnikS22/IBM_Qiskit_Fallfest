# results/: every figure and number, and what produced it

Nothing here is typed in by hand. Each file is written by the script or notebook listed next to it, and rerunning
that produces it again.

## Figures

| File | What it shows | Produced by |
|---|---|---|
| `01_phantom.png` | The layered 3D head phantom (water, scalp, skull, brain, bleed) | notebook 01 |
| `01_traces.png` | Receiver energy traces on the 7³ head: exact solver (lines) vs finite differences (dotted) | notebook 01 |
| `02_cost_accuracy.png` | Accuracy vs gate cost for the compact and unary encodings, 1D–3D | notebook 02 |
| `03_noise.png` | Ideal vs FakeKingston noise vs mitigation (post-selection, ZNE) as Trotter steps grow | notebook 03 |
| `05_fwi.png` | Classical FWI recovering the bleed on a 104 × 104 slice (1,576 vs true 1,578 m/s) | notebook 05 |
| `05_hybrid_shots.png` | Hybrid quantum-misfit bleed search: success rate vs shots per circuit | notebook 05 |
| `06_stride_validation.png` | Our solver vs Stride on the same 2D head slice (correlation 0.993) | `validation/compare_stride.py` |
| `07_crossover.png` | Accuracy-matched speed crossover, classical vs IBM Heron gate time | `scaling/crossover.py` |

## Real IBM hardware (v1)

| File | Contents |
|---|---|
| `hardware_ibm_marrakesh.json` | Analysed results for all 6 circuits from job `db9smd9gv2cc73e60pm0` on `ibm_marrakesh`: raw and post-selected values, standard errors, shots kept, ideal and exact references |
| `03_hardware_results.json` | Same content, under the file name notebook 03 reads |
| `hw_run.log` | Console log of the submission (`hardware/run_notebook03_hw.py`) with the job ID |
| `hardware_fake_kingston_DRYRUN.json` | The free rehearsal of the same 6 circuits on the FakeKingston noise model (300 shots) |
| `03_noise_results.json` | Noise-model sweep from notebook 03 (FakeKingston, 4,000 shots) |

Raw bitstring counts and IBM job metadata (timestamps, measured QPU usage of 9 s) are in
[`../project/handoff/3_ibm_job/`](../project/handoff/3_ibm_job/).

## Hardware campaign v2 (rehearsals)

`hardware_campaign/*_fake_marrakesh_DRYRUN.json` and `hardware_v2_fake_marrakesh_DRYRUN.json` are **rehearsals on the
FakeMarrakesh noise model**, not real-hardware results. They cover experiments E1–E6 from `hardware/campaign.py` (time trace,
repeats, ablation, Estimator, size, 2D); see `EXPERIMENTS.md` §5. Real runs would be written as `*_ibm_*.json`.

## Validation and speed numbers

| File | Contents | Produced by |
|---|---|---|
| `stride_comparison.json` / `.npz` | Trace correlations and raw traces, our solver vs Stride | `validation/compare_stride.py` |
| `07_crossover.json` | Accuracy-matched step counts, classical timings, Heron gate times, fitted scaling, crossover, full-head projection, assumptions | `scaling/crossover.py` |
