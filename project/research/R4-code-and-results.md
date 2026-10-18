# R4 — Code & results audit: team-quantum-ultrasound ("Aperion")

Source: `/Users/aniksahai/Downloads/team-quantum-ultrasound.zip`, unzipped (treated as untrusted) to
`/Users/aniksahai/Desktop/IBM Quantum Hackathon/code/team-quantum-ultrasound/`. All numbers below come from saved notebook
outputs or the results JSON files. I did **not** run any team code. To check the numbers, I wrote a small numpy/scipy
re-implementation of the 1D 7-cell Hamiltonian myself and ran it from the scratchpad with `python -I`. Every number from
that check is marked **[my check]**.

**Headline status**
- **Real IBM hardware: NOT run.** `RUN_ON_IBM = False` (nb03 cell 9). There is no `results/03_hardware_results.json`, no job ID and no backend name. Every "IBM noise" number comes from the **FakeKingston noise model** (local Aer).
- **No credentials committed.** The API key is read with `getpass` at run time (`qwave/hardware.py:80`). Nothing needs revoking.
- Circuits vs classical on a noiseless simulator: **done** in 1D (15 q unary / 4 q compact), 2D 3×3 (33 q / 6 q) and 3D 3×3×3 (135 q unary on the MPS simulator). The 3D compact count is an estimate only.
- Classical FWI baseline: **done**, in 2D on a laptop.
- Hybrid: **classical emulation only.** It uses exact `expm` plus multinomial shot sampling. No circuit was built.
- Validation against Stride, the paper group's own software: **done** (2D, 5 cm slice).

---

## 1. What the code does

### 1.1 The physics and the exact Hamiltonian (`qwave/encoding.py`, `qwave/grid.py`)
- **Grid** (`grid.py`): an N-D box of cells (vertices) joined by links (edges). Every boundary cell also gets a "ghost" edge to a fixed zero-pressure node, which gives a Dirichlet, reflecting, energy-conserving box. Edge count: E = Σ_axes (cells/n_a)·(n_a+1). For 7 cells in 1D that is **8 edges** (6 interior + 2 ghost).
- Incidence matrix B (V×E): −1 at the lower endpoint of each edge, +1 at the upper endpoint.
- **Coupling** (default `form="paper"`): **K = diag(c) · B**. With q = p/c, the wave equation **q_tt = −K Kᵀ q** becomes
  **p_tt = c² ∇²p**. This is the constant-density acoustic equation used by Guasch 2020 and Stride (proved in `test_paper_form_is_the_papers_equation`).
  The older Costa graph form is `form="graph"`: K = B·diag(c_edge), i.e. p_tt = ∇·(c²∇p), which corresponds to a density ∝ 1/c².
- **Hamiltonian**: **H = [[0, iK], [−iKᵀ, 0]]** on the (V+E)-dimensional space. It is Hermitian, so ψ(t) = e^{−iHt} ψ(0) is unitary and conserves energy.
  - ψ(0) = |source vertex⟩, i.e. a unit velocity kick at one cell.
  - The read-out is |ψ_r(t)|². In the vertex block this is the kinetic-energy fraction (q_t)², not pressure.
  - Units: speeds are normalised by 1500 m/s, dx = 1, and t is in grid units.
- **Compact (binary) encoding**: basis state |k⟩ ↔ site k. Qubits = ⌈log₂(V+E)⌉. H is zero-padded to 2ⁿ and Pauli-decomposed with `SparsePauliOp.from_operator`. This only works for ≤10 qubits (there is an assert).
- **Unary (one-hot) encoding**: one qubit per site, so qubits = V+E. The wave is a single excitation hopping on the vertex–edge graph. Each bond (a,b,h) becomes the Pauli terms Re(h)/2·(XX+YY) and Im(h)/2·(YX−XY), which are exact inside the 1-excitation subspace (`test_unary_hamiltonian_equals_wave_hamiltonian_in_subspace`). Bonds are greedily coloured into layers of disjoint pairs. In 1D this gives 2 layers.

### 1.2 Circuits (`qwave/circuits.py`)
- `compact_circuit`: X gates prepare |source⟩, then one `PauliEvolutionGate(op, t, SuzukiTrotter(order=2, reps=steps))`.
- `unary_circuit`: X on the source qubit, then `steps` repetitions of a second-order Strang sequence over the layers: L₀(dt/2) … L_last(dt) … L₀(dt/2).
- `gate_cost`: `transpile(basis=[cz, rz, sx, x], opt=1)` with **no coupling map** (all-to-all), reporting CZ count and depth.
- Read-outs:
  - `compact_receiver_probs`: Statevector of the decomposed circuit.
  - `unary_receiver_probs`: Aer `save_expectation_value` of Z_r, using statevector up to 22 qubits and MPS above that.
- `compact_cz_estimate`: Σ 2(w−1) CZ over the Pauli weights, × 2 × steps. This is an analytic estimate, not a compiled circuit.
- `qwave/subspace.py` replays the unary Trotter circuit exactly inside the 1-excitation subspace. It is used for large grids and shows that the unary encoding is classically easy. Its docstring cites `tests/test_subspace.py`, which does not exist; the test lives in `test_quantum.py`.

### 1.3 Classical baseline (`qwave/classical.py`, `qwave/fwi.py`, `validation/compare_stride.py`)
- `classical.py` has two independent solvers for the same operator:
  - velocity-Verlet finite differences (dt = 2e-3);
  - exact `expm_multiply` of H.
  - `total_energy_fd` checks that energy is conserved.
- `fwi.py` is a 2D classical FWI in JAX:
  - 104×104 grid, 2.5 mm cells, 32-transducer ring, 60 kHz Ricker pulse, 776 time steps, Gaussian sponge boundary;
  - Adam optimiser (lr 3.0, 40 iterations, mini-batch of 8 sources);
  - the gradient comes from reverse-mode autodiff, which equals the discrete adjoint;
  - like the paper's Fig. 8 test, the skull is known and the brain starts homogeneous.
- `compare_stride.py` runs the same 2D 5 cm slice through Stride/Devito (Imperial) and through their own FD solver:
  - 0.5 mm grid, 200 kHz 3-cycle tone burst, 16 transducers, dt = 0.04 µs, 1400 steps;
  - Stride cases: A = paper physics; B = density K₀/c², i.e. the Costa graph form; C = A + approximate skull attenuation.
  - The Mosaic logs in `mosaic-workspace/` confirm Stride actually ran (2026-10-17 14:04, OT2 kernel, 10.5 points per wavelength).

### 1.4 Head phantom (`qwave/phantom.py`)
- Speeds (m/s): water 1500, scalp 1600, skull 2800, brain 1546, blood 1578 (+2%).
- The head is an ellipsoid. Each layer is at least 1 cell thick.
- `ray_through` takes the 1D line through the centre of the 3D phantom.
- `transducers` returns the outermost head cells.

### 1.5 Hardware, noise and mitigation (`qwave/hardware.py`, notebook 03)
- **Problem.** The ear-to-ear ray through a 7×7×7 phantom gives a 7-cell line plus 8 edges = **15-qubit unary circuit**.
  - The source is qubit 0 (left scalp). The receiver is qubit/vertex 2 (the first brain cell). t = 1.5.
  - The bleed variant puts blood in the centre cell (cell 3).
- **Circuit sweep.** steps 2/4/6/8 at fold 1, plus fold 3 at 8 steps (ZNE), plus the bleed case at 8 steps: 6 circuits in total.
- **Transpile.** `generate_preset_pass_manager(optimization_level=3, backend, seed_transpiler=7)`.
- **Modes.**
  - `ideal`: Aer MPS, 4000 shots, so the "ideal" values carry shot noise.
  - `fake`: `AerSimulator.from_backend(FakeKingston())`, 4000 shots, `seed_simulator=7`, **a single repeat**.
  - `ibm`: `QiskitRuntimeService(channel="ibm_quantum_platform")`, `least_busy`, `Batch`, `SamplerV2` with dynamical decoupling and gate + measurement twirling. Not executed.
- **Mitigation.**
  - **Post-selection**: keep only Hamming-weight-1 bitstrings, since the physics conserves one excitation.
  - **ZNE**: global unitary folding U(U†U)^k with barriers, at scales 1 and 3, linear extrapolation ZNE = 1.5·r₁ − 0.5·r₃.
  - **DD + twirling**: hardware path only. The FakeKingston simulation does not apply them.

### 1.6 Resources and 3D (`qwave/resources.py`, notebook 04)
- The paper's head is 22 cm at 0.5 mm = 440³ cells. That gives V = 85,184,000 and E = 256,132,800, so the **compact encoding needs 29 qubits** and the **unary encoding needs 341,316,800 qubits**.
- Trotter steps needed: the smallest power of two that reaches 5% accuracy at the crossing time t = n, on grids 3³–11³.
- Unary CZ cost: CZ per bond per step (measured on 3³) × 2E × steps, with steps scaled linearly from 11³.
- **Read-out wall**:
  - shots per circuit = (1−p)/(p·ε²) with p = 1e-3 and ε = 1%;
  - number of circuits = 1024 sources × 1000 time samples;
  - IBM time = 2 s/job + 0.35 ms/shot.

### 1.7 Hybrid (`qwave/hybrid.py`, notebook 05 Part B)
- Setup: 7×7×7 head, compact encoding (11 qubits), 20 candidate models (no bleed, or a bleed in one of 19 brain cells).
- One surface cell is the source; the other 97 surface cells are receivers. Times are 2, 3 and 4.
- "Quantum" misfit: a multinomial sample of the exact |ψ|² over all sites, with S shots. The "measured" data are the exact energies of the true head.
- The classical part takes the argmin over the 20 candidates, with 20 trials per shot count.

### 1.8 End-to-end pipeline
1. Classical baseline: FD = exact to 7e-8 in 3D, Stride agreement 0.993, 2D FWI recovers the bleed.
2. Hamiltonian H = [[0, iK], [−iKᵀ, 0]] with K = diag(c)B.
3. Two encodings: compact log₂(V+E) and unary V+E.
4. Second-order Trotter circuits.
5. Transpilation to the CZ basis, and to ISA circuits for FakeKingston.
6. Noiseless simulator vs exact.
7. Noisy FakeKingston simulation, with real hardware still pending.
8. Post-selection + ZNE.
9. Analysis of bleed contrast vs error bar.
10. 3D estimates: 29 qubits compact, unary qubits and CZ count, read-out shots, hybrid shot requirement.

---

## 2. Every concrete result (with source)

### 2.1 Grid and qubit counts (nb02 cell 3)

| Grid | Cells V | Links E | Compact qubits | Unary qubits |
|---|---|---|---|---|
| 1D (7,) | 7 | 8 | **4** | **15** |
| 2D (3,3) | 9 | 24 | 6 | 33 |
| 3D (3,3,3) | 27 | 108 | 8 | 135 |
| 3D (7,7,7) | 343 | 1176 | 11 | 1519 |
| Paper 440³ (nb04 cell 1) | 85,184,000 | 256,132,800 | **29** | 341,316,800 |
| 2×2×2 [my check; not in repo] | 8 | 36 | 6 | 44 |

**7³ phantom tissue counts** (nb01 cell 3), as [water, scalp, skull, brain, blood]: [164, 98, 62, 18, 1].

**Phantoms that are too small to contain a brain** (my arithmetic on `head_phantom`):
- **3×3×3**: 8 water corners, 18 scalp, 1 skull centre, **no brain at all**.
- **2×2×2**: all 8 cells are scalp.

### 2.2 Noiseless circuit vs classical (nb02 cell 5)
Setup: t = 1.5, source = first cell along axis 0. Error is the max |error| over two receivers (far end, centre). CZ counts are transpiled with opt=1, all-to-all.

| Grid | Encoding | Steps | Qubits | CZ | Max error |
|---|---|---|---|---|---|
| 1D | unary | 2 / 4 / 8 | 15 | 70 / 126 / **238** | 1.36e-3 / 6.3e-4 / **1.7e-4** |
| 1D | compact | 2 / 4 / 8 | 4 | 336 / 694 / **1414** | 2.87e-3 / 4.9e-4 / **1.1e-4** |
| 2D 3×3 | unary | 2 / 4 / 8 | 33 | 234 / 450 / 882 | 0.0252 / 0.0148 / 0.0038 |
| 2D 3×3 | compact | 2 / 4 / 8 | 6 | 8602 / 17916 / 36416 | 0.0100 / 0.0013 / 0.00027 |
| 3D 3×3×3 | unary | 2 / 4 / 8 | 135 | 1134 / 2214 / 4374 | 0.145 / 0.029 / **0.0057** |
| 3D 3×3×3 | compact (estimate) | 2 / 4 / 8 | 8 | 363,904 / 727,808 / 1,455,616 | not run |

- Compact vs unary at 8 steps: 2D ≈ **41×** more CZ (36416/882); 1D ≈ 5.9×.
- **Caveat [my check].** In 1D at t = 1.5 the two receivers (vertex 6 and vertex 3) carry an exact signal of only **0.0000 and 0.00136**. The 1D "max error 1.7e-4" is therefore measured on near-empty receivers. On a receiver that actually has signal (vertex 2, exact 0.1040), 8-step unary Trotter gives 0.1015, an error of **0.0025** (2.4%). That matches nb03's noiseless 0.1013.

### 2.3 Classical checks
- **Energy conservation, 7³** (nb01 cell 5): 1.000002 / 1.000004 / 1.000003 at t = 1 / 3 / 6.
- **FD vs exact solver, 7³**, 41 times up to t = 8 (nb01 cell 7): max difference **7.0e-8**.
- **Bleed effect, 7³** (nb01 cell 9): the largest change at any of 3 receivers is **3.14e-4** absolute, which is 10.7% of that receiver's peak signal.
- **Stride comparison** (`results/stride_comparison.json`):

| Comparison | Relative RMS error | Mean trace correlation |
|---|---|---|
| ours (lap), 1× grid vs Stride A | 0.147 | 0.977 |
| ours (lap), 2× grid vs Stride A | 0.071 | 0.9926 |
| ours (lap), 3× grid vs Stride A | 0.071 | **0.9933** |
| ours (graph), 3× vs Stride B | 0.056 | 0.9885 |
| Stride B vs A (Costa form vs paper physics) | 0.448 | **0.756** |
| Stride C vs A (skull attenuation on vs off) | 0.018 | 0.9997 |

- **2D FWI** (nb05 cells 1–2):
  - 104×104 grid, 776 time steps.
  - Misfit by iteration: 1.94e-5 (it 1) → 3.14e-5 (it 10) → 1.09e-5 (it 20) → 3.33e-6 (it 30) → **1.30e-6** (it 40).
  - **Bleed true 1578.0 m/s, recovered 1576.3 m/s.** Surrounding brain recovered as 1546.3 (true 1546).
  - Wall-clock time was not recorded. The README's "seconds" is not measured.

### 2.4 Noise / mitigation results (`results/03_noise_results.json`, nb03 cells 1–7)
- **Problem.** Healthy ray [scalp, skull, brain, brain, brain, skull, scalp] = [1600, 2800, 1546, 1546, 1546, 2800, 1600] m/s. The bleed ray has 1578 at the centre cell.
- **Exact energy at the receiver:** healthy **0.104034**, bleed **0.104081**, a difference of **4.7e-5**. My check reproduces these exactly.
- **Backend:** FakeKingston noise model in local Aer, 4000 shots, **1 repeat**, seed 7. Error bars below are binomial standard errors only.

| Case | CZ (ISA) | Depth (ISA) | Ideal (sampled) | Raw ± SE | Post-selected ± SE | Kept |
|---|---|---|---|---|---|---|
| 2 steps | 70 | 45 | 0.0633 | 0.0383 ± 0.0030 | 0.0548 ± 0.0043 | 69.8% |
| 4 steps | 126 | 75 | 0.0923 | 0.0478 ± 0.0034 | 0.0823 ± 0.0057 | 58.0% |
| 6 steps | 182 | 104 | 0.1073 | 0.0473 ± 0.0034 | 0.0923 ± 0.0064 | 51.2% |
| **8 steps** | **238** | **130** | 0.1013 | **0.0468 ± 0.0033** | **0.0958 ± 0.0067** | 48.8% |
| 8 steps, fold 3 | 714 | 388 | 0.1008 | 0.0170 ± 0.0020 | 0.0817 ± 0.0095 | 20.8% |
| 8 steps, bleed | 238 | 130 | 0.1015 | 0.0440 ± 0.0032 | 0.0905 ± 0.0065 | 48.6% |

- **ZNE at 8 steps** (nb03 cell 7), exact = 0.1040:
  - raw counts: 0.0467 → **0.0616 ± 0.0051**;
  - post-selected counts: 0.0958 → **0.1028 ± 0.0111**.
- **Error vs exact** (my arithmetic from the table):

| Read-out | Absolute error | Relative error |
|---|---|---|
| Raw | 0.057 | 55% |
| Post-selected | 0.008 | 7.9% |
| Post-selected + ZNE | 0.001 | 1.2%, but the SE is ±11% |
| ZNE on raw counts only | 0.042 | 41% |

- **Bleed vs healthy, post-selected:** 0.0905 ± 0.0065 vs 0.0958 ± 0.0067. The exact difference (5e-5) is about 140× smaller than the SE.
- **QPU plan** (nb03 cell 9): 6 circuits × 4000 shots ≈ **10 s** estimated, out of 600 s. Not executed.

### 2.5 3D and scaling (nb04)
- **Trotter steps for 5% accuracy at t = n**: 3³ → 256, 5³ → 64, 7³ → 64, 9³ → 128, 11³ → 256 (non-monotone; no growth law was fitted).
- **Unary CZ per bond per step** (3³): **3.42**.
- **Paper head, unary**: 3.41e8 qubits, ≥ ~1e4 steps, **≥ ~2e13 CZ** per simulation. This is a linear extrapolation, not a measured value.
- **Paper head, compact**: 29 qubits. No gate count; it would need block-encoding.
- **Read-out wall**: 1.0e9 numbers per FWI iteration, so **1.0e13 shots**:
  - **114 years** per iteration at the IBM rule-of-thumb rate;
  - 118 days at a 1 MHz shot rate;
  - the paper's GPU target for the whole reconstruction is <10 min.

### 2.6 Hybrid (nb05 cell 3)
Setup: 11 qubits, 20 candidates, 97 receivers, true bleed at (3, 3, 4). With infinite shots the misfit picks the correct candidate.

| Shots per circuit | Correct location | QPU estimate per search |
|---|---|---|
| 1e6 | 0% | 0.2 days |
| 1e8 | 5% | 24 days |
| 1e9 | 5% | 243 days |
| 1e10 | **50%** | 2,431 days |
| 1e11 | **95%** | 24,306 days |

Random guessing gives 5%. `run_detection` (the yes/no question) exists in the code but was **never run** in the notebook.

### 2.7 Things that do not exist in the repo
- No IBM job IDs.
- No real backend name.
- No hardware JSON.
- No repeated runs (seeds).
- No timing or runtime benchmarks, for either classical or quantum.
- No pytest output saved. The README claims 35 tests; the count of 35 is correct, but there is no proof that they pass.
- No 2×2×2 circuit run.
- No circuit diagram figure.

---

## 3. Deck claims: confirmed or contradicted

| Deck claim | Verdict | Evidence |
|---|---|---|
| 7 cells: scalp, skull, skull, brain, skull, skull, scalp | **Contradicted** | The ray is **scalp, skull, brain, brain(bleed), brain, skull, scalp** (`test_ray_goes_through_skull_and_bleed` asserts labels [1,2,3,4,3,2,1]; nb03 cell 1 prints 1600, 2800, 1546, 1546/1578, 1546, 2800, 1600). |
| Compact: 4 qubits, ~1,100 two-qubit gates | **Qubits confirmed; gate count wrong** | At t = 1.5 the CZ count is 336 / 694 / **1,414** at 2 / 4 / 8 steps (nb02). ~1,100 matches no run. Use "1,414 CZ at 8 steps" (all-to-all; more with real connectivity). |
| One-qubit-per-site: 15 qubits (7 cells + 8 edges), ~240 gates | **Confirmed** | 238 CZ at 8 steps (nb02), and 238 CZ / depth 130 after ISA transpile for FakeKingston (nb03). |
| Circuit matches classical on simulator | **Confirmed, with a caveat** | 1D unary 8 steps: max error 1.7e-4 (but on near-zero receivers; 0.0025 on the signal-bearing receiver). 3D 3×3×3 unary: 0.0057. |
| Hardware run with mitigation still to do | **Confirmed** | Not run. Post-selection + ZNE were done on FakeKingston only. |
| 3D: smallest 2×2×2 grid on simulator [status unknown] | **Contradicted / replace** | 2×2×2 was never run, and the phantom at 2×2×2 is all scalp. What ran is **3×3×3, 135-qubit unary, MPS simulator, error 0.0057 at 8 steps, 4,374 CZ** (that phantom has no brain cell). Compact 3×3×3 (8 qubits) is an estimate only: ~1.46M CZ. |
| Full head ~29 qubits (estimate) | **Confirmed (estimate)** | 440³: log₂(341,316,800) = 28.35, so 29. State register only; no ancillas or gate count. |
| Hybrid: quantum estimates one number (misfit), classical does the rest | **Design confirmed; status = classical emulation** | No circuit was built. Exact `expm` plus multinomial sampling. Needs 1e10–1e11 shots per circuit. |

**What actually ran**

| Done (real computation) | Simulator only | Estimate only | Not done |
|---|---|---|---|
| Classical FD/exact 3D; Stride comparison; 2D FWI | Noiseless circuits 1D/2D/3D; FakeKingston noise + post-selection + ZNE (1 seed); hybrid shot study (emulated) | Compact 3D CZ; 440³ qubits/CZ/steps; read-out wall; QPU days | IBM hardware; 2×2×2; repeats; timings |

---

## 4. Slide-by-slide fill list

- **baseline (classical 1D)**
  - 7-cell ray: scalp 1600 | skull 2800 | brain 1546 | brain 1546 (bleed: 1578) | brain 1546 | skull 2800 | scalp 1600 m/s.
  - Equation p_tt = c²∇²p, Dirichlet box, kick at left scalp, read energy at the first brain cell at t = 1.5.
  - Exact answer **0.1040** (bleed 0.1041).
  - Two solvers agree to 7e-8 (3D 7³) and energy is conserved to 4e-6.
  - Credibility line: "Our solver matches the paper group's Stride software: 0.993 correlation."
  - Optional second panel: 2D FWI recovers the bleed (1576 vs 1578 m/s).
- **mapping**
  - H = [[0, iK], [−iKᵀ, 0]], K = diag(c)·B.
  - Compact: 4 qubits (⌈log₂ 15⌉), 1,414 CZ at 8 steps.
  - Unary: 15 qubits (7 cells + 8 links), 238 CZ at 8 steps, nearest-neighbour XX+YY / XY−YX gates.
  - Circuit diagram: not in the repo. Generate with `unary_circuit(g, c, 1.5, 1, 0).decompose().draw("mpl")` for one Trotter step (2 bond layers).
- **extend3d**
  1. 1D 7 cells: circuits done (simulator).
  2. 2D 3×3: done (33 q unary, 6 q compact).
  3. 3D 3×3×3: unary 135 q done on the MPS simulator (error 0.0057, 4,374 CZ); compact 8 q is an estimate only (~1.5M CZ).
  4. 7³ (11 q compact): classical/emulated only.
  5. 440³: estimate (29 q compact; 3.4e8 q unary; ≥2e13 CZ).
  - Drop "2×2×2".
- **code** (real API, matches `qwave/circuits.py` and `hardware.py`, ≤8 lines):
  ```python
  qc = QuantumCircuit(15); qc.x(0)                      # kick at left scalp (unary: 1 qubit per cell/link)
  dt = t / steps
  for _ in range(steps):                                 # 2nd-order Trotter over 2 bond layers
      qc.append(PauliEvolutionGate(L0, dt/2), range(15))
      qc.append(PauliEvolutionGate(L1, dt),   range(15))
      qc.append(PauliEvolutionGate(L0, dt/2), range(15))
  qc.measure_all()
  isa = generate_preset_pass_manager(optimization_level=3, backend=backend).run(qc)   # 238 CZ, depth 130
  ```
- **design**
  - Metric: energy fraction at receiver qubit 2, compared with the exact 0.1040.
  - Success criterion: |mitigated − exact| within 2 SE, and less than the raw error.
  - Runs table, as it stands: 6 circuits (steps 2/4/6/8, fold 3 at 8, bleed at 8) × 4,000 shots × **1 repeat** on FakeKingston; hardware 0.
  - Change to "× 3 repeats" once the runs in section 6 are done.
- **simresults**
  - Noiseless: 1D unary max error 1.7e-4 at 8 steps (2.4% on the signal-bearing receiver); 3D 3×3×3 0.0057 at 8 steps.
  - FakeKingston at 8 steps: raw 0.047 ± 0.003, post-selected 0.096 ± 0.007, + ZNE 0.103 ± 0.011, exact 0.104.
  - Bleed detected? **No.** The difference is 5e-5 against an SE of 0.007, and this receiver/time choice barely sees the bleed (see section 6).
- **hardware**
  - Currently: "pending."
  - Fill after the run: backend (`ibm_kingston` or whichever `least_busy` returns), job ID, ISA depth (expect ~130) and CZ count (expect 238), DD + gate/measurement twirling + post-selection + 2-point ZNE, raw → post → ZNE vs 0.104.
  - Never put FakeKingston numbers on this slide without a label saying "noise model".
- **scaling**
  - Qubits vs grid: compact 4 / 6 / 8 / 11 / 29; unary 15 / 33 / 135 / 1519 / 3.4e8.
  - CZ at 8 steps: compact 1,414 / 36,416 / ~1.46M (estimate); unary 238 / 882 / 4,374.
  - Read-out wall: 1e13 shots per FWI iteration, about 114 years.
- **limits**
  - No absorption.
  - Reflecting box.
  - Energy read-out, not pressure.
  - Unary encoding is classically simulable.
  - Compact encoding needs block-encoding / fault tolerance.
  - Read-out wall.
  - Hybrid needs 1e10–1e11 shots per circuit.
  - Toy phantoms (3³ has no brain).
  - Noise model, not hardware.
  - Single seed.
- **roadmap**
  1. Run on hardware tonight.
  2. Bleed-sensitive receiver/time.
  3. Block-encoded compact circuits (Schade / Bösch 2024).
  4. Non-unitary absorption (Schrödingerisation).
  5. Few-number clinical outputs (bleed yes/no via amplitude estimation instead of sampling).

## 5. Figures → slides

| Slide | File | Notes |
|---|---|---|
| baseline | `results/06_stride_validation.png` | Use the middle trace panel. **No code in the repo generates this PNG**, so be ready to explain where it came from. The "1.000" bar is really 0.9997. |
| baseline | `results/01_traces.png`, `results/01_phantom.png` | Show the phantom slices. |
| baseline / roadmap | `results/05_fwi.png` | Classical FWI recovers the bleed. |
| simresults / scaling | `results/02_cost_accuracy.png` | Error vs CZ for both encodings. |
| simresults / hardware | `results/03_noise.png` | Depth sweep and shots kept. |
| limits / hybrid | `results/05_hybrid_shots.png` | |

**Graphs to generate**
1. Bar chart of 8-step exact / ideal / raw / post / post+ZNE / raw-ZNE with SE bars, from `03_noise_results.json`. Add the hardware bars next to it after the run.
2. Qubits vs grid size (log scale) for both encodings, from the table in 2.1.
3. Circuit diagram of one Trotter step (15 qubits).
4. Bleed contrast vs time per receiver for the 7-cell ray, from the exact solver. This shows why t = 1.5 at qubit 2 cannot see the bleed; see section 6.

## 6. Bugs, errors, overclaims and tonight's priorities

### Bugs, physics and maths issues
1. **The hardware experiment is blind to the bleed by construction.**
   - At t = 1.5 the wave has barely reached cell 2, and the bleed is in cell 3. The exact difference is 4.7e-5 [my check].
   - The verdict "bleed not detectable on today's hardware" therefore comes mostly from the chosen receiver and time, not from the hardware.
   - **[my check]** exact contrasts at later times:

| Time | Receiver | Healthy | Bleed − healthy | 8-step Trotter value |
|---|---|---|---|---|
| t = 5.5 | vertex 3 | 0.128 | −0.014 | −0.0097 |
| t = 4.5 | vertex 3 | 0.110 | +0.0066 | +0.0071 |
| t ≈ 10.5–10.75 | vertex 6 (far scalp, physical) | 0.29–0.47 | ±0.023 | — |

   - At t = 5.5, 238 CZ is enough to keep most of the contrast.
   - The far-scalp case needs ≥32 steps (~900 CZ), which is too deep for hardware.
2. **The nb02 1D "max error vs classical" is computed on near-zero receivers** (exact 0.0000 and 0.0014 at t = 1.5). Report error on a receiver that has signal, or report relative error.
3. **The 3×3×3 "3D head" has no brain** (1 skull cell, 18 scalp, 8 water), and 2×2×2 is all scalp. Say "3D heterogeneous grid", not "3D head".
4. **Docstring sign error in `encoding.py`.** With φ = [q_t; Kᵀq], −iHφ gives q_tt = +KKᵀq. The consistent state is φ = [q_t; −Kᵀq]. The physics and read-out are unaffected because the evolution is still unitary and |vertex|² = q_t², but correct the slide or paper equation if you show φ.
5. **Noise-model and sampling caveats.**
   - FakeKingston numbers come from 1 seed and 4,000 shots. The "ideal" column is shot-sampled (0.1073 > exact at 6 steps is shot noise).
   - The simulation applies no DD or twirling, so simulator and hardware runs are not configured the same way.
6. **ZNE caveats.** Two points, linear fit. The post-selected ZNE error bar (±0.011, ~11%) is as large as the correction (0.0958 → 0.1028), so "matches exact" is also consistent with no improvement. The fold-3 circuit keeps only 21% of shots.
7. **Overclaims and wording.**
   - nb03 calls the bleed result "measured, honest", but it is simulated.
   - README "Tested (notebook 05)" for the quantum misfit is an emulation.
   - "Laptop FWI in seconds" was not timed.
   - FWI uses an inverse crime: the same solver generates and inverts the data, with no noise.
   - Gate counts in nb02 assume all-to-all connectivity; the compact 4-qubit circuit on heavy-hex/Heron will need SWAPs.
   - Stride case C uses an approximate attenuation in loosely specified units, on a skull only ~1.5 mm thick, so "absorption changes signals ~2%" probably understates it.
   - The 3D "≥2e13 CZ lower bound" is an extrapolation, not a proven bound.

### Tonight's 3–5 priorities (≤10 min Open Plan)
1. **Run the existing 6-circuit set on real hardware.**
   - Set `RUN_ON_IBM = True` in nb03 and use `ibm_kingston`/`least_busy`, so the +5 hardware bonus is earned.
   - Do **3 repeats** (3 × 6 × 4,000 = 72k shots, about 30–60 s of QPU time with overhead).
   - Save backend, job IDs, ISA depth and CZ count to `03_hardware_results.json`.
   - Report raw → post-selected → post+ZNE against 0.1040, with mean ± std over repeats.
2. **Add a bleed-sensitive pair to the hardware run**: t = 5.5, receiver vertex 3, 8 steps (238 CZ), healthy vs bleed, about 20k shots each.
   - Expected Trotter contrast is −0.0097 [my check]. Even a ~2σ result, or an honest null, is a far stronger story than measuring at t = 1.5.
   - Simulate it first on FakeKingston.
3. **Repeat the FakeKingston runs over 5 seeds** (both `seed_simulator` and `seed_transpiler`), with DD/twirling noted as absent. This gives real error bars and a fair simulator-vs-hardware comparison.
4. **Strengthen ZNE**: add fold 5 (3-point Richardson or exponential fit) at 8 steps. Optionally replace the hand-rolled method with readout-error mitigation, using measurement twirling plus calibration of the 15 measured qubits.
5. **Fix the slides**: the 7-cell order, compact gates = 1,414 (not ~1,100), 3D = 3×3×3 / 135 q (not 2×2×2), hybrid labelled "emulated", and nb02 errors reported on the signal-bearing receiver.
   - Also run `pytest -q` once and screenshot "35 passed" for Results & Validation.
