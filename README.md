# Can a quantum computer see a brain bleed?

**One sentence:** we turned the sound-wave simulation behind a proposed portable stroke scanner (Guasch et al.,
*npj Digital Medicine* 2020) into quantum circuits, proved they reproduce the physics in 1D, 2D and 3D, measured what
real IBM noise does to them, and worked out what the paper's full 3D head would need. Our conclusion: quantum fits
the physics, but it isn't a practical fit for this pipeline yet.

See `USE-CASE.md` for the clinical problem and `LIMITATIONS.md` for what the results can't support.

## The pipeline and where quantum is used

| Stage of the brain-imaging pipeline | Quantum? | Why |
|---|---|---|
| Simulate sound through a guessed head (the expensive step) | **Tested** (notebooks 02–04) | Wave physics maps exactly onto quantum evolution; the real head fits in 29 qubits |
| Compare simulated vs. recorded signals (one mismatch number) | **Tested** (notebook 05) | One number is cheap to read out; full recordings are not |
| Update the head model (gradient for ~10⁸ unknowns) | Classical | The adjoint method already costs about 2 simulations |
| Escape wrong answers (cycle skipping) | Classical (AWI in the paper) | No quantum route beats it |
| Image → diagnosis | Classical | Nothing for quantum to exploit |

## Repository layout

```
qwave/                  the package (plain Python files)
  grid.py               1D/2D/3D grids as graphs of cells + links
  phantom.py            layered head: water, scalp, skull, brain, blood
  classical.py          classical solvers (finite differences + exact)
  encoding.py           quantum encodings: compact (log qubits) and unary (one qubit per cell/link)
  circuits.py           Qiskit circuits, simulators, gate counts
  subspace.py           fast classical replay of the unary circuit (for big grids)
  hardware.py           ear-to-ear ray through the 3D head: noisy sim / real IBM hardware
  hybrid.py             quantum misfit + classical search for the bleed
  fwi.py                classical full-waveform inversion baseline (JAX)
  resources.py          scaling to the paper's 440³ head and the read-out wall
tests/                  37 automated checks (pytest): physics = encoding = circuits
validation/             compare_stride.py: our solver vs. the researchers' Stride software
hardware/               campaign.py (v2 test campaign), run_ibm_v2.py, run_ibm.py (v1): see RUN_HARDWARE.md
EXPERIMENTS.md          every experiment: question, method, settings, success criterion, results
notebooks/              01–05, the story with figures (run in order)
results/                figures + JSON numbers written by the notebooks
```

## How to run

```bash
pip install -r requirements.txt
pytest -q                         # ~30 s: proves quantum circuits reproduce the classical wave in 1D, 2D, 3D
jupyter lab notebooks/            # run 01 → 05
```

- **Laptop or Colab:** everything. Notebook 03's noisy simulations take about 10–20 min; the others take seconds to a couple of minutes.
- **Cluster (optional):** larger noise sweeps, or 3D FWI on a GPU node (`pip install "jax[cuda12]" qiskit-aer-gpu`).
- **Real IBM hardware:** follow `RUN_HARDWARE.md` (`python hardware/run_ibm.py`, current IBM runtime API). The key is read
  from the environment and never saved. About 6 circuits × 4,000 shots ≈ 10–30 s of the 10 free minutes.

## How we know it works (the tests)

| Test | What it proves |
|---|---|
| `test_energy_conserved`, `test_exact_matches_finite_difference` | The classical 3D model is right: two independent solvers agree to about 1e-7 |
| `test_paper_form_is_the_papers_equation` | The quantum rulebook encodes exactly the paper's equation p_tt = c²∇²p |
| `test_unary_hamiltonian_equals_wave_hamiltonian_in_subspace` | The qubit Hamiltonian *is* the wave equation, exactly |
| `test_compact_circuit_matches_classical`, `test_unary_circuit_matches_classical` | Gate-by-gate circuits reproduce the wave in 1D, 2D and **3D (135 qubits)** |
| `test_trotter_error_shrinks_with_steps` | Circuit error converges as circuits get deeper |
| `test_fwi_gradient_points_toward_bleed`, `test_hybrid_exact_misfit_finds_bleed` | The inversion pipelines find the bleed |

## Validation against the researchers' software (Stride)

`validation/compare_stride.py` runs the same 2D head slice (5 cm, 0.5 mm grid, 16 transducers, 200 kHz pulse) through
[Stride](https://github.com/trustimaging/stride), the open-source ultrasound software from the paper's group, and
through our solver. It needs a separate Python 3.11 environment with Stride + Devito installed.

| Comparison | Mean trace correlation |
|---|---|
| Our solver vs. Stride, paper physics (p_tt = c²∇²p) | **0.993** (≈7% residual from source/receiver handling) |
| Our Costa-form solver vs. Stride with matching density | 0.989 |
| Original Costa-form physics vs. paper physics | 0.756: a different medium, so we switched the quantum encoding to the paper form |
| Stride with vs. without skull absorption (approximate value) | 0.9997: absorption, which the quantum form omits, changes signals by ~2% here |

![Stride validation](results/06_stride_validation.png)

## Key results

| Question | Result | Notebook |
|---|---|---|
| Does the quantum circuit reproduce the wave in 3D? | Yes: 3×3×3 head, 135 qubits, error 0.006 vs. classical at 8 steps | 02 |
| Cost of the compact (memory-saving) encoding | About 40× more gates in 2D; about 10⁶ CZ for a 3×3×3 head (estimate) | 02 |
| What IBM-level noise does (FakeKingston, 8 steps, 238 CZ; exact 0.104) | Raw 0.047 ± 0.003 (signal halved) → post-selected 0.096 ± 0.007 (keeps 49% of shots) → + ZNE 0.103 ± 0.011. ZNE alone on raw counts: 0.062 | 03 |
| **Real IBM hardware v1** (ibm_marrakesh, 15 qubits) | Raw loses ~87% of the signal; post-selection recovers all points to within 2σ of the ideal circuit; ZNE fails; chip ~3× noisier than its noise model | EXPERIMENTS.md §4 |
| Bleed detectable on today's hardware? | No: the exact signal change (0.00005) is ~100× below the error bar | 03 |
| Real 3D head (paper scale) | 29 qubits compact; unary needs 3×10⁸ qubits and at least ~10¹³ CZ (lower bound) | 04 |
| Read-out for one FWI iteration | About 10¹³ shots, about 114 years at today's IBM rate (paper's GPU target: under 10 min total) | 04 |
| Classical FWI baseline | Recovers the 2% bleed in 2D on a laptop (1,576 vs. true 1,578 m/s) | 05 |
| Hybrid quantum misfit → bleed location | 50% correct at 10¹⁰ shots, 95% at 10¹¹ shots per circuit: decades of QPU time | 05 |
| Better than classical? | **No** on accuracy, speed and readout; the only advantage is theoretical memory (29 qubits) | all |

**Recommendation:** use classical GPUs for this pipeline now. Quantum becomes worth revisiting with fault-tolerant
hardware running structured (block-encoded) compact circuits, *and* a clinical question that needs only a few numbers out.

## What is and isn't new (prior work)

Already published: the wave-equation-to-Hamiltonian mapping (Costa et al. 2019); 1D heterogeneous circuits
(Suau et al. 2021; Schade et al. 2024, run on IBM Brisbane); a 2D heterogeneous acoustic circuit in simulation
(Sato et al. 2024); a 3D heterogeneous quantum-FWI framework in theory (Bösch et al. 2024); one-hot/unary encodings
for other PDEs (Leng, Wu et al.). **Apparently new (moderate confidence, based on a literature search):**
the medical/transcranial application; a verified 3D heterogeneous circuit implementation; the paper-physics
coupling validated against Stride; unary encoding with excitation-number post-selection on the wave equation, compared
head-to-head with the compact encoding; and the noise and hybrid-readout analysis. These are application and
engineering contributions, not a new algorithm.

## Sources
- Guasch, Calderón Agudo, Tang, Nachev, Warner. *Full-waveform inversion imaging of the human brain.* npj Digital Medicine 3:28 (2020). https://doi.org/10.1038/s41746-020-0240-8
- Costa, Jordan, Ostrander. *Quantum algorithm for simulating the wave equation.* PRA 99, 012323 (2019). https://arxiv.org/abs/1711.05394
- Schade, Bösch, Hapla, Fichtner. *A quantum computing concept for 1-D elastic wave simulation with exponential speedup.* GJI 238(1) (2024) (Qiskit, IBM Brisbane). https://arxiv.org/abs/2312.14747
- Suau, Staffelbach, Calandra. *Practical quantum computing: solving the wave equation using a quantum approach.* ACM TQC (2021). https://arxiv.org/abs/2003.12458
- Sato, Tezuka, Kondo, Yamamoto. 2D acoustic wave with varying speed via Hamiltonian simulation (2024). https://arxiv.org/abs/2407.05019
- Bösch, Schade, Aloisi, Keating, Fichtner. Quantum wave simulation framework incl. 3D and loss functions (2024). https://arxiv.org/abs/2411.17630
- Leng, Li, Peng, Wu. *Hamiltonian embedding* (unary/one-hot encodings). Quantum 9, 1857 (2025). https://quantum-journal.org/papers/q-2025-09-11-1857/
- Cueto et al. *Stride: a flexible software platform for high-performance ultrasound computed tomography* (2022). https://github.com/trustimaging/stride
- IBM Quantum docs: Open Plan limits, job run-time estimation, error mitigation. https://quantum.cloud.ibm.com/docs
