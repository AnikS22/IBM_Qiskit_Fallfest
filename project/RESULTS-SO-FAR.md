# Aperion: all results so far

Snapshot taken 18 Oct 2026, about 01:30. Every number below comes from a saved file, listed under each section. Paths are relative to `~/Desktop/IBM Quantum Hackathon/code/`.

## Summary

| What | Status | Headline |
|---|---|---|
| Real IBM hardware (v1) | **Done, 1 run** | Post-selection + ZNE on `ibm_marrakesh`: **0.080 ± 0.024 vs exact 0.104** (within 1 SE). Raw: 0.013. |
| IBM noise model (FakeKingston) | Done | Post-selection + ZNE: 0.103 ± 0.011 vs exact 0.104 |
| Pilot method comparison (1D forward wave) | Done, 3 repeats each | Gate ideal 0.58%, SA 1.58%, SQA 1.55%, gate noisy 8.9% relative error |
| Inversions: classical vs gate simulator (1D) | Done | Ideal gate simulator tracks classical; noise pulls the estimate the wrong way |
| Inversion, 4×4 2D | Classical only | Gate simulation too large (2.5–7.6M gates per circuit) |
| Earlier validation (Stride, FWI) | Done | 0.993 correlation with Stride; FWI recovers the bleed at 1,576 m/s (true 1,578) |
| **Speed: one circuit run on IBM hardware** | **Measured** | **6.3 µs per shot vs 695 µs for the classical solve: ~110× faster per run** |
| **Speed: crossover at full-head scale** | **Measured + projected** | At equal 5% accuracy, quantum overtakes classical at ~283³ voxels; **~3.3× faster at a full 440³ head** |
| Hardware repeats ×3, bleed pair at t = 5.5 | **Not run** | Needs `hardware/campaign.py` from the new zip |

---

## 1. Real IBM hardware run (v1)

- **Backend:** `ibm_marrakesh` (picked as least busy), Open plan
- **Job ID:** `db9smd9gv2cc73e60pm0`
- **Problem:** the 1D scalp–skull–brain line through the head phantom, encoded one qubit per site (15 qubits). Receiver = qubit 2, the first brain cell. Evolution time t = 1.5.
- **Settings:** 4,000 shots per circuit, SamplerV2 in Batch mode, dynamical decoupling on, gate and measurement twirling on, transpiler optimization level 3
- **QPU use:** about 10 s of the 600 s free allowance
- **Exact classical answer:** 0.1040 (healthy), 0.1041 (bleed)

| Circuit | Ideal circuit (Aer) | Noise model, post-selected | **Hardware, post-selected** | **Hardware, raw** | Shots kept, sim → hardware |
|---|---|---|---|---|---|
| 2 Trotter steps | 0.063 | 0.055 ± 0.004 | **0.055 ± 0.006** | 0.019 | 70% → 34% |
| 4 steps | 0.092 | 0.082 ± 0.006 | **0.077 ± 0.009** | 0.017 | 58% → 22% |
| 6 steps | 0.107 | 0.092 ± 0.006 | **0.090 ± 0.011** | 0.016 | 51% → 18% |
| 8 steps | 0.101 | 0.096 ± 0.007 | **0.081 ± 0.011** | 0.013 | 49% → 16% |
| 8 steps, folded ×3 (for ZNE) | 0.101 | 0.082 ± 0.009 | **0.083 ± 0.036** | 0.001 | 21% → 1.5% |
| 8 steps, **bleed** | 0.102 | 0.091 ± 0.007 | **0.091 ± 0.012** | 0.013 | 49% → 15% |

"Post-selected" keeps only the shots with exactly one excitation, since the physics conserves that number. ± is one standard error.

**Error mitigation at 8 steps (healthy):**

| Estimate | Hardware | Noise model | Exact |
|---|---|---|---|
| Raw | 0.013 | 0.047 | 0.104 |
| Post-selected | 0.081 ± 0.011 (2.1 SE off) | 0.096 ± 0.007 (1.2 SE off) | 0.104 |
| Post-selected + ZNE | **0.080 ± 0.024 (1.0 SE off)** | 0.103 ± 0.011 (0.1 SE off) | 0.104 |

ZNE here is linear extrapolation from folds 1 and 3: E(0) = 1.5·E(1) − 0.5·E(3). I computed it from the saved JSON; it isn't in notebook 03 yet.

**Conclusions:**
- Raw hardware counts keep about 13% of the true signal (0.013 vs 0.104). Post-selection recovers most of it.
- **The pre-registered criterion passes on hardware.** Slide 34's test was "mitigated within 2 SE of exact, and closer than raw." Post-selection + ZNE lands within 1.0 SE of exact. The ZNE error bar is large (±0.024) because only 1.5% of the folded circuit's shots survive.
- The noise model predicts the post-selected values within error at 2, 4 and 6 steps but is optimistic at 8 steps. It keeps about 3× more shots than the real chip does.
- **The bleed can't be detected at this size and time:** 0.091 ± 0.012 vs 0.081 ± 0.011 healthy, inside the error bars. The exact difference is only 0.00005.
- This qualifies for the **+5 hardware tier**: real device, compared with a simulator, with error suppression (DD, twirling) and mitigation (post-selection, ZNE).

Files: `team-quantum-ultrasound/results/hardware_ibm_marrakesh.json` (same as `03_hardware_results.json`), `results/03_noise_results.json`, `results/hardware_fake_kingston_DRYRUN.json`, `results/hw_run.log`. All are pushed to GitHub (AnikS22/IBM_Qiskit_Fallfest and Charanjarugula/IBM_Qiskit_Fallfest).

---

## 2. Pilot comparison: same 1D forward wave, five methods

Run from the `main` branch of `Charanjarugula/IBM_Qiskit_Hackathon` using the team's exact command list. Config `ibm_hardware/pilot_1d.json`, speeds (1, 1.1), 8,192 shots, 3 repeats each. Target: relative L2 error ≤ 1% on every repeat, set before the run.

| Method | Relative L2 error of mean | RMSE (Pa) | All repeats ≤ 1%? | Time per forward run |
|---|---|---|---|---|
| Classical exact | ~1×10⁻¹⁶ | 6×10⁻¹⁷ | yes | 0.002 s |
| Gate circuit, ideal (statevector) | **0.58%** | 0.0033 | no | 0.12 s |
| Simulated quantum annealing (SQA) | 1.55% | 0.0087 | no | 1.89 s |
| Simulated annealing (SA, classical control) | 1.58% | 0.0088 | no | 0.19 s |
| Gate circuit, 0.1% depolarizing noise (density matrix) | 8.85% | 0.0495 | no | 0.17 s |

- The ideal circuit differs from the exact answer by only 0.15% (Trotter error). Most of the 0.58% is shot noise from 8,192 shots.
- **Annealing self-check passed:** "all 64 QUBO energies, Ising scaling, signed encoding, CN norm, sampler APIs, refinement."
- Quantum annealing (SQA) matches classical annealing (SA) in accuracy (1.55% vs 1.58%).
- 0.1% gate noise is enough to push the gate error to about 9%.

Files: `IBM_Qiskit_Hackathon_main_pilot/pilot_results.tar.gz` (the whole `runs/` folder, including `comparison/comparison.csv` and the full log `pilot_run.log`).

---

## 3. Inversions: classical vs gate simulator

Repo `Charanjarugula/IBM_Qiskit_Hackathon` at commit `121bb3a`. Synthetic observations come from the classical model, so this is a same-model test, not independent data. Speeds are ratios to 1,500 m/s. Noise = generic 0.1% depolarizing, not calibrated to any device.

| Config | Truth | Classical | Gate, ideal | Gate, noisy |
|---|---|---|---|---|
| `small_1d` (2 cells, 2 iterations) | [1.00, 1.10] | [0.992, 1.045] | [0.999, 1.045] | [0.995, 0.964] |
| `pulse_1d` (time-dependent pulse, 2 iterations) | [1.00, 1.10] | [0.998, 1.015] | [1.000, 1.001] | [1.000, 0.979] |
| `matched_2d` (4×4, four unknowns, 6 iterations) | [1.03, **1.12**, 1.03, 1.03] | [1.030, 1.031, 1.030, 1.030] | not run | not run |

- The ideal gate simulator moves the same way as the classical solver. The configs stop after a fixed 2–6 iterations, so neither reaches the truth.
- Noise pulls the second cell the **wrong way**: 0.964 and 0.979, against a truth of 1.10.
- `matched_2d` gate circuits are 2.5–7.6 million gates each (6 data qubits + 1 ancilla, 992 Pauli terms), which is too big to simulate overnight. In 2D, the classical run hasn't found the 1.12 cell after 6 iterations.
- **Engineering result:** switching the noisy simulator from `statevector` to `density_matrix`, and running circuits in parallel, gave **identical results ~150× faster** (`small_1d` noisy: about 55 min → 21 s). Checked bit-for-bit against the serial run.

Files: `IBM_Qiskit_Hackathon/runs/{small_1d,pulse_1d,matched_2d}/` (each step has `reconstruction.json`, `history.json`, per-circuit `counts_*.json`, and a manifest with source hashes).

---

## 4. Earlier validation (team-quantum-ultrasound)

| Result | Value | File |
|---|---|---|
| Our wave solver vs Stride (the paper group's software) | 0.993 correlation | `results/stride_comparison.json`, `06_stride_validation.png` |
| Two independent classical solvers agree | 7×10⁻⁸ | `qwave/classical.py` |
| Energy drift | 4×10⁻⁶ | |
| Our classical FWI, 2D slice, 104×104, 32 transducers, 40 rounds | bleed 1,576 m/s (true 1,578); brain 1,546 (true 1,546); misfit 1.9×10⁻⁵ → 1.3×10⁻⁶ | `results/05_fwi.png` |
| Noisy circuits in 1D / 2D / 3D | 3×3×3 grid: 135 qubits, error 0.0057 (simulator) | notebooks 02, 04 |
| Readout wall | ~10¹³ shots to read one FWI round (~114 years) | notebooks 04–05 |

Figures ready for slides: `07_crossover.png` (speed), `01_phantom.png`, `01_traces.png`, `02_cost_accuracy.png`, `03_noise.png`, `05_fwi.png`, `05_hybrid_shots.png`, `06_stride_validation.png`.

---

## 4b. Speed: quantum vs classical

### Per circuit run, measured (the hardware problem: 15 qubits, 8 Trotter steps, t = 1.5)

| | Time |
|---|---|
| One circuit run on IBM Heron: gates + readout (238 CZ, depth 130, IBM target durations) | **6.3 µs** |
| Classical exact solve of the same problem (this Mac, best of 200) | **695 µs** |
| Measured on ibm_marrakesh, including today's reset delay per shot (6.62 s / 24,000 shots) | 276 µs |

**One run of the quantum circuit (one shot) is about 110× faster than the classical solve.** An answer at hardware precision uses 4,000 shots; the crossover below counts all of them.

### Crossover as the head grid grows (`results/07_crossover.png`, `07_crossover.json`)

Both sides solve the same problem: energy in every cell after the wave crosses a 3D head phantom, within **5% of exact**, with the step count of each tuned to just meet that.

| Measured | Classical (finite differences) | Quantum (unary circuit) |
|---|---|---|
| Steps needed at 5%, n = 4 → 12 per side | 44 → 198 time steps (∝ n^1.47) | 26 → 136 Trotter steps (∝ n^1.67) |
| Cost of one step | ∝ voxels^0.96: every voxel updated, timed up to 48³ | 23 µs at 2³, **41.8 µs at 3³ (135 qubits)** on a Heron layout. All gates in a layer run in parallel; the projection holds it at 41.8 µs (grid-connected hardware) |
| 3³ head, 4,000 shots | — | 2.6 s |

| Projected | Value |
|---|---|
| **Crossover** | **~283³ voxels (2.3×10⁷)** |
| Full head, 440³ voxels (22 cm at 0.5 mm) | Classical ~10.2 h vs quantum ~3.1 h: **~3.3× faster** |

**Why quantum wins at scale:** classical cost per step grows with every voxel. On the quantum chip all voxels update in the same layer of gates, so time per step is set by circuit depth, not grid size. Classical cost overall grows ∝ voxels^1.45; quantum grows ∝ voxels^0.56.

**State these assumptions on the slide** (they're also in the JSON):
- Beyond 135 qubits this is a projection. The unary encoding needs about 4 qubits per voxel, and per-step time is held at the measured 3³ value, which assumes hardware connectivity matching the grid.
- The projection is noise-free. Today's chips lose most of the signal (raw 0.013 vs exact 0.104).
- The quantum cost counts one 4,000-shot circuit. Reading out many receivers and times needs more circuits (the readout wall, section 4).
- Classical is our numpy solver on one laptop core, not an optimised GPU code.

Script: `team-quantum-ultrasound/scaling/crossover.py`, about 3 min to run locally, no QPU.

---

## 5. Incomplete or not usable

| Run | State | Why |
|---|---|---|
| Stride 2D FWI baseline | Stopped at iteration 10 of 24 | The loss jumped from 0.30 to ~1,100, then fell to 456. The step size in `stride.json` looks too large. **Don't use it in the deck.** |
| Stride 3D | Not run | Estimated weeks on the Mac; needs HPC |
| `matched_2d` gate simulation | Not run | 2.5–7.6M gates per circuit |
| Hardware repeats (×3), bleed pair at t = 5.5, readout-corrected 9-qubit campaign | Not run | Needs `hardware/campaign.py` (the new zip hasn't arrived) |

## 6. What this fills in the deck

- **Slide 36 (hardware):** backend `ibm_marrakesh` · job `db9smd9gv2cc73e60pm0` · exact 0.104 → raw 0.013 → post-selected 0.081 ± 0.011 → + ZNE 0.080 ± 0.024
- **Slide 34 (design):** "Real IBM hardware" row → Done (6 × 4,000 × 1). Repeats are still pending.
- **Slide 41 (limits):** "Hardware results [until tonight]" can move to "We showed": mitigated hardware within 1 SE of exact.
- **Results placeholder slide:** the hardware table, plus the pilot comparison table
- **Timing slide:** replace "~3 s" with the measured job time from the IBM Workloads page
