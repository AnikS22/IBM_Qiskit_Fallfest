# Experiment log and methods

This file records every experiment: the question, the method, the settings, the pre-registered success criterion,
and the result. Numbers come from files in `results/`; nothing here is typed in by hand without a source file,
including the v1 hardware table (from `results/hardware_ibm_marrakesh.json`; run log with job id in `results/hw_run.log`;
the script the laptop used is `hardware/run_notebook03_hw.py`).

## 0. What is being tested

The paper (Guasch et al. 2020) images the brain with full-waveform inversion (FWI). Its expensive step is simulating
sound travelling through a guessed head. We encode that simulation as quantum evolution (Hamiltonian simulation,
Costa et al. 2019) and test it in four stages:

| Stage | Question | Where |
|---|---|---|
| A. Classical correctness | Is our wave simulator right? | `tests/test_physics.py`, notebook 01, `validation/compare_stride.py` |
| B. Quantum correctness | Do the quantum circuits compute the same physics? | `tests/test_quantum.py`, notebook 02 |
| C. Noise (simulated) | What would IBM-chip noise do, and do our fixes help? | notebook 03 |
| D. Real hardware | What does a real IBM chip actually do? | `hardware/`, this file §4–5 |
| E. Scale | What would the paper's full problem need? | notebook 04, 05 |

## 1. Classical correctness (stage A)

* Two independent classical solvers (finite differences; exact matrix exponential) agree to ~1e-7 in 1D/2D/3D;
  energy is conserved to 1e-5 (`tests/test_physics.py`).
* **Against the researchers' software (Stride, Imperial College; AGPL-3.0, called as an external tool, not copied):**
  same 2D head slice (5 cm, 0.5 mm grid, 16 transducers, 200 kHz). Our solver vs Stride: mean trace correlation
  **0.993**. The original Costa "graph" form models a different medium (0.756 vs the paper's physics), so the quantum
  encoding uses a corrected "paper" coupling, proven equal to p_tt = c²∇²p by `test_paper_form_is_the_papers_equation`.
  Skull absorption (which unitary quantum evolution cannot include) changed signals by ~2% (approximate attenuation value).

## 2. Quantum correctness (stage B, noiseless simulators)

* The qubit Hamiltonian equals the wave operator exactly in the single-excitation subspace (test).
* Gate-level circuits match classical: 1D error 0.0002, 2D 0.004, **3D (3×3×3 head, 135 qubits) 0.006** at 8 Trotter steps.
* Errors shrink with more steps (2nd-order Trotter, ~4× per doubling).
* Encodings: compact (log₂ qubits; 29 for the real head) needs ~40× more gates in 2D and ~1.5×10⁶ CZ for 3×3×3;
  unary (one qubit per cell/link) is hardware-friendly but has no memory advantage.

## 3. Simulated noise (stage C, FakeKingston, 15-qubit ray, 4,000 shots)

At 8 steps (238 CZ), exact 0.104: raw 0.047 ± 0.003 → post-selected 0.096 ± 0.007 (49% kept) → + ZNE 0.103 ± 0.011.

## 4. Real hardware v1 (ibm_marrakesh, job `db9smd9gv2cc73e60pm0`, 2026-10-17)

15 qubits (ear-to-ear line through the 3D head), t = 1.5, 6 circuits × 4,000 shots, dynamical decoupling + gate
twirling, ~10 s QPU. Exact answer 0.104; "ideal" = noiseless circuit with the same number of steps.

| Case | Ideal circuit | Raw | Post-selected | Kept | Gap |
|---|---|---|---|---|---|
| Healthy, 2 steps | 0.063 | 0.019 | 0.055 ± 0.006 | 34% | 1.3σ |
| Healthy, 4 steps | 0.092 | 0.017 | 0.077 ± 0.009 | 22% | 1.7σ |
| Healthy, 6 steps | 0.107 | 0.016 | 0.090 ± 0.011 | 18% | 1.5σ |
| Healthy, 8 steps | 0.101 | 0.013 | 0.081 ± 0.011 | 16% | 1.8σ |
| Healthy, 8 steps, ×3 folded | 0.101 | 0.001 | 0.083 ± 0.036 | 1.5% | — |
| Bleed, 8 steps | 0.101 | 0.013 | 0.091 ± 0.012 | 15% | — |

Findings: raw hardware loses ~87% of the signal; post-selection recovers every point to within 2σ; the real chip
keeps ~3× fewer shots than the noise model predicted (16% vs 49%); ZNE fails because the ×3 circuit is almost all
noise; the bleed is not detectable (its true effect is 0.00005).

## 5. Real hardware v2 campaign (`hardware/campaign.py`)

Lessons from v1 drove three changes:
1. **Light-cone truncation:** within t ≤ 3 only the first 4 cells influence the receiver, so 9 qubits replace 15
   (max difference vs the full line < 0.001; enforced by `test_light_cone_truncation_is_valid`). Gates drop ~40%.
2. **Readout-error correction** (`qwave/readout.py`): two calibration circuits (all-0, all-1) give each qubit's
   readout error; the exact tensored inverse is applied to all 512 outcomes, then post-selection. Tested by
   `test_readout_correction_recovers_true_distribution`. Error bars by bootstrap over data and calibration shots.
3. **A time trace** instead of single numbers: t = 0.5 … 3.0 (wave arrives through the skull, peaks, leaves).

**Pre-registered success criterion (written before any v2 hardware run):** the readout-corrected, post-selected
trace is within 2 standard errors of the ideal circuit at ≥ 5 of 6 times, **and** its correlation with the exact
classical trace is ≥ 0.9.

| Exp. | Question | Circuits | Est. QPU |
|---|---|---|---|
| E1 trace | Does the chip reproduce the wave arrival? (main) | 2 cal + 6 times + 2 folds | ~16 s |
| E2 repeat | Reproducible? (2 more runs, different qubit layouts) | 2 × 10 | ~32 s |
| E3 ablation | Which suppression helps: none / DD / twirling / both? | 4 × 4 | ~25 s |
| E4 estimator | IBM's built-in mitigation (levels 0/1/2) vs our post-selection | 3 jobs × 2 | ~30 s |
| E5 size | 15-qubit vs 9-qubit version of the same physics | 2 × 4 | ~12 s |
| E6 2D (optional) | Is a 2D grid feasible on hardware today? (16 qubits, 198–370 CZ) | 4 | ~7 s |

The script stops before exceeding `--max-seconds` (default 900, estimated). Rehearsal on FakeMarrakesh
(1,000 shots, `results/hardware_campaign/*_DRYRUN.json`): criterion met in E1 and both E2 repeats (6/6 points,
correlation 0.99); the simulated chip is known (from v1) to be optimistic, so the real result may be worse.

**Real v2 results: to be filled in from `results/hardware_campaign/*_ibm_*.json` after the run.**

## 6. Reproduce everything

```bash
pip install -r requirements.txt
pytest -q                                            # 37 checks, ~30 s
jupyter lab notebooks/                               # 01-05
python hardware/campaign.py --dry-run --with-2d      # free rehearsal, ~15 min
IBM_QUANTUM_TOKEN=... python hardware/campaign.py --backend ibm_marrakesh --with-2d
# Stride validation (separate Python 3.11 env with Stride + Devito): python validation/compare_stride.py
```
