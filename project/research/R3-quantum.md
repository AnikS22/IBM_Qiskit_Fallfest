# R3: Quantum research for Aperion (Qiskit Fall Fest 2026)

Compiled 2026-10-17. Every row was checked against the primary source: arXiv PDFs were downloaded and grepped, IBM pages were fetched on 2026-10-17, and DOIs were resolved through doi.org/Crossref.

Confidence key:
- **H** means verified verbatim in the primary source.
- **M** means verified in a secondary source, or derived by us from verified numbers.
- **L** means our own estimate or unverified. Label these as estimates on any slide.

Equation-location numbers ("eq. 25", "§5.2") refer to the arXiv PDF version cited in the row.

---

## 1. Schade, Bösch, Hapla & Fichtner (2024): 1-D elastic wave on IBM Brisbane

Citation: M. Schade, C. Bösch, V. Hapla, A. Fichtner, "A quantum computing concept for 1-D elastic wave simulation with exponential speedup", *Geophys. J. Int.* **238**(1), 321–333 (2024), doi:10.1093/gji/ggae160. arXiv:2312.14747 (v1 22 Dec 2023, v2 7 May 2024). Bösch and Schade contributed equally (ETH Zurich). Code: https://github.com/malteschade/Quantum-Wave-Equation-Solver (HTTP 200 on 2026-10-17).

| Claim | Number / Equation | Source | Exact quote / location | Conf. |
|---|---|---|---|---|
| PDE solved | ρ(x) ∂tt u = ∂x[µ(x) ∂x] u, with ∂x u(0,t)=0 and u(W,t)=0 | [arXiv:2312.14747v2](https://arxiv.org/abs/2312.14747) | Eq. (11), §3 | H |
| Semi-discrete system | M ∂tt u = K u, with K = −DᵀED (M = diag ρ, E = diag µ, D = forward FD matrix) | same | Eqs. (12)–(16) | H |
| Mass transform and first-order form | ũ = M^{1/2}u, K̃ = M^{-1/2}KM^{-1/2}; ∂t[ũ; ṽ] = [[0, 1],[K̃, 0]] [ũ; ṽ] = Q[ũ; ṽ] | same | Eq. (17); "Q the impedance matrix" | H |
| Cholesky factor | U = E^{1/2} D M^{-1/2}, K̃ = −UᵀU | same | Eqs. (22)–(23): "which is an analytical Cholesky decomposition" | H |
| **Hamiltonian (slide equation)** | **H = i T Q T⁻¹ = i [[0, U], [−Uᵀ, 0]]**, with T = diag(U, 1) | same | Eq. (25): "where H is Hermitian, meaning that it can be employed as a Hamiltonian" | H |
| **Schrödinger form (slide equation)** | **i ∂t\|ϕ(t)⟩ = H\|ϕ(t)⟩**, \|ϕ(0)⟩ = T[M^{1/2}u₀; M^{1/2}v₀] | same | Eqs. (19)–(20) | H |
| Sparsity | 2-sparse H for 2nd-order FD in 1-D | same | §3: "It produces a Hamiltonian with two entries per row (2-sparse)" | H |
| Encoding | Amplitude (binary) encoding. n qubits hold 2^{n−1} displacement + 2^{n−1} velocity entries; with general BCs the grid holds 2^{n−1}−1 points | same | §3 ("2^{n−1} grid points"); App. C: "this formulation allows for 2^{n−1} − 1 grid points for n qubits" | H |
| Normalisation | \|ψ(0)⟩ = \|ϕ(0)⟩/‖\|ϕ(0)⟩‖, undone at the end | same | Eqs. (26)–(27) | H |
| **Time evolution on hardware was NOT Trotterized** | Exact U(t) = e^{−iHt} was built classically and compiled, using Qiskit `PauliEvolutionGate` and the "scaling and squaring method (Al-Mohy and Higham, 2010)" | same | §4: "The unitary time evolution for a particular evolution time, U(t), is constructed classically and decomposed into quantum gates." The method "becomes inapplicable due to the exponential scaling" | H |
| Trotter / qubitization was analysed in theory only | Qubitization needs O(d t ‖H‖max + log(1/ε)) oracle queries | same | App. B | H |
| Hardware run | IBM Brisbane (127-qubit Eagle), **7 grid points** | same | §4: "requiring us to scale the problem down to 7 grid points" | H |
| Qubit count on hardware | 7 grid points with n = 4 by App. C (2^{n−1}−1 = 7). The circuit figure shows a 4-qubit Pauli observable (XZXZ), but the text says "5 qubits" | same | §4: "average circuit depth of 870 quantum gates with 5 qubits"; Fig. A1: "XZXZ Pauli observable" | M (internal inconsistency: cite as "4–5 qubits") |
| Gate count | ~870 gates average circuit depth | same | §4 | H |
| Their noise estimate | 0.999^870 ≈ 0.42 success probability, based on EPLG 1.9 % | same | §4 | H |
| Readout method | Full quantum state tomography (QST) with 2^n Pauli observables (state is real), 1000 shots per circuit | same | §4 | H |
| **Hardware result** | RL2 error **up to 60 %** on Brisbane vs ~3 % from QST shot noise alone | same | §4: "qualitative agreement … however with RL2 errors of up to 60 %" | H |
| Simulator result | 128-point problem: RL2 ≈ 20 % (20 shots) and ≈ 4 % (1000 shots); error ∝ 1/√S | same | §4, Fig. 1 | H |
| Error mitigation used? | None reported. Only "more advanced error mitigation methods" is mentioned as future work | same | §4 last para | H (absence) |
| Hardware limits size | "currently limiting the problem size to 7 grid points" | same | §4 | H |
| **Readout kills speedup** | QST needs exponentially many runs | same | §4: "Reading out the final state therefore requires exponentially many HS passes, nullifying any speedup from HS." §5.2: "the read-out would nullify the exponential speedup" | H |
| Initial state prep | Sparse state prep is O(nS) gates for S nonzeros (Gleinig & Hoefler). On hardware they used a 3-gate point source | same | App. B; App. D | H |
| Speedup claim and its condition | Polynomial in n, polylog in N, *assuming oracles* and ε, d, ‖H‖max independent of n | same | App. B: "This establishes the exponential speedup over classical solutions." | H (claim). Contradicted in practice by §1b below |
| Limitations stated | Attenuation is impossible under unitary HS; sources are missing; higher dimensions are not done | same | §5.4: "HS is inherently unitary and hence can only simulate systems that conserve energy" | H |
| Memory claim | 101 qubits for a whole-Earth wavefield at mm³ resolution | same | §5.1 | H |
| Brisbane has since been retired | ibm_brisbane retired 2025-11-03 | [IBM retired QPUs](https://quantum.cloud.ibm.com/docs/en/guides/retired-qpus) | Table: "ibm_brisbane 127 2025-11-03" | H |

### 1b. Follow-up by the same group, which tempers "exponential"

Citation: C. Bösch, M. Schade, G. Aloisi, S. D. Keating, A. Fichtner, "Quantum wave simulation with sources and loss functions", *Phys. Rev. Research* **7**, 033225 (2025), doi:10.1103/t8wt-mp2l, [arXiv:2411.17630](https://arxiv.org/abs/2411.17630).

| Claim | Number | Source | Quote / location | Conf. |
|---|---|---|---|---|
| Practical speedup is **polynomial**, not exponential | Quadratic (1D), cubic (2D), quartic (3D) | [arXiv:2411.17630](https://arxiv.org/abs/2411.17630) §III | "the obtainable speed-up is usually only polynomial … we expect a quadratic speed-up in 1D, cubic in 2D, and quartic in 3D" | H |
| Why | Wave travel time t = O(N^{1/D}); classical O(N^{1+1/D}) vs HS Õ(N^{1/D}) | same §III | "let t = O(N^{1/D}) represent the simulation time for the signal to reach the domain boundary" | H |
| Condition on the speedup | Needs global measurements and compact sources | abstract | "under conditions of sufficiently global measurements and compactly supported sources and initial conditions" | H |
| Loss-function readout | l2 misfit on a subvolume S with O(M log(1/δ)/ε) state-prep calls (amplitude estimation, Theorem 2) | same §III, Thm 2 | "achieving optimal precision scaling with the number of samples taken" (abstract) | H |

---

## 2. Costa, Jordan & Ostrander (2019)

Citation: P. C. S. Costa, S. Jordan, A. Ostrander, "Quantum algorithm for simulating the wave equation", *Phys. Rev. A* **99**, 012323 (2019), [arXiv:1711.05394](https://arxiv.org/abs/1711.05394) (v4, 20 Dec 2019).

| Claim | Number / Equation | Source | Exact quote / location | Conf. |
|---|---|---|---|---|
| PDE | d²φ/dt² = c²∇²φ (c = 1) | [arXiv:1711.05394](https://arxiv.org/abs/1711.05394) | Eq. (1) | H |
| Discrete form | d²φ/dt² = −(1/a²) L φ, with L = graph Laplacian | same | Eq. (3) | H |
| **Hamiltonian (slide equation)** | **H = (1/a) [[0, B], [B†, 0]]** | same | Eq. (4): "Hermitian independent of the specific choice of matrix B" | H |
| Why it works | H² = (1/a²) diag(BB†, B†B), so if BB† = L the vertex block obeys the wave equation | same | Eqs. (6)–(7): "So, if BB† = L then a subspace of the full Hilbert space evolves according to a discretized wave equation." | H |
| B = signed incidence matrix | \|V\|×\|E\|, entries ±√W_j | same | Eq. (8), §2 | H |
| Hilbert space | H = H_V ⊕ H_E; dimension \|V\|+\|E\| | same | Eq. (9); "the dimension of the Hilbert space H is equal to the number of vertices of the graph plus the number of edges" | H |
| What edges mean | Edge amplitudes are auxiliary variables that come from making the system first order | same | §2: "extra variables that necessarily arise when converting second order differential equations into first order" | H |
| What the final state encodes | φ(T) on vertices; edge block ∝ B⁻¹ dφ/dt | same | §10: "a state which encodes both φ(T) and B⁻¹ dφ(T)/dt" | H |
| **Qubit count** | n = ⌈log₂((1+D)(l/a)^D)⌉; sparsity ≤ 2D; ‖H‖max = 1/a | same | §2, text after Eq. (9) | H |
| Gate complexity | g = Õ(t D²/a) for HS; state prep Õ(D^{5/2} l/a) | same | Eq. (11); Introduction | H |
| Classical comparison | Classical needs Ω((l/a)^D) time to output the full field | same | Introduction | H |
| Dirichlet BC trick | Add weighted self-loops at boundary vertices | same | §3, Fig. 2 | H |
| **Readout caveat 1 (output is samples)** | Measuring gives samples ∝ \|amplitude\|² (intensity) | same | Introduction: "By measuring this state one obtains a sample from a distribution proportional to the square of the amplitude" | H |
| **Readout caveat 2 (vertex-subspace probability unbounded)** | Probability of landing in H_V can be ~0 | same | §10: "In general we cannot give a reasonable lower bound on the success probability of this measurement, even for simple systems." | H |
| Velocity extraction | Needs phase estimation plus a rotation; success ∝ κ(L)⁻² worst case | same | §10, Eqs. (90)–(91) | H |

---

## 3. Other quantum wave / seismic / FWI work, 2019–2026 (for "is 'first' defensible?")

| Paper | What it did | Hardware? | Source | Quote / location | Conf. |
|---|---|---|---|---|---|
| Suau, Staffelbach, Calandra, *ACM TQC* 2(1), 2021, doi:10.1145/3430030 | Implemented Costa et al. with Trotter (k = 1); gate count fit O(N_d^{3/2} log²N_d), λ ≈ 3×10⁵ | Circuit timing from IBM Q gate data (not executed at scale); N_d = 32 simulated | [arXiv:2003.12458](https://arxiv.org/abs/2003.12458) | Abstract: "the constants hidden in the big-O notation were huge enough to make the solver less efficient than classical solvers for reasonable discretisation sizes"; Fig. 4a, eq. (23); Fig. 2: logical→physical "3 to 4 orders of magnitude" | H |
| Wright et al. (Quantinuum + bp), *PRR* 6, 043169 (2024) | 1-D isotropic (homogeneous, periodic) acoustic wave; depth O(n²); infidelity O(2^{−4n}t²) | **Quantinuum H1-1**, n = 6 (+1) qubits, 10,000 shots | [arXiv:2402.19247](https://arxiv.org/abs/2402.19247) | Abstract; Fig. 2 caption: "n = 6 qubits … Nshots = 10,000" | H |
| Schade et al., GJI 2024 | **Heterogeneous** 1-D elastic, 7 points | **IBM Brisbane** | §1 above | — | H |
| Bösch et al., PRR 2025 | Sources, l2 loss functions, acoustic/elastic/Maxwell; quartic 3-D speedup | Theory + simulation | [arXiv:2411.17630](https://arxiv.org/abs/2411.17630) | §1b | H |
| Babbush, Berry, Kothari, Somma, Wiebe, *PRX* 13, 041041 (2023) | Exponential speedup for 2^n coupled oscillators (kinetic-energy estimation, BQP-complete) | Theory | [arXiv:2303.13012](https://arxiv.org/abs/2303.13012) | Abstract: "solves a potentially practical application with an exponential speedup". Bösch et al. note this needs *non-local* couplings | H |
| Jin & Zhang 2025 | Elastic waves via Schrödingerisation, variable media | Theory | [arXiv:2505.18711](https://arxiv.org/abs/2505.18711) | Abstract | H |
| Nakanishi, Yano, Sato 2026 | **Explicit Trotter circuits and CNOT counts**, 3-D elastic, homogeneous media | Numerics | [arXiv:2604.20284](https://arxiv.org/abs/2604.20284) | Table I: 1st-order Trotter time O((log N)³ T²v²/(h²ε)); 2nd-order O((log N)^{7/2} T^{3/2}v^{3/2}/(h^{3/2}ε^{1/2})); "Spatial discretization error, source terms, state preparation, readout, and fault-tolerance overhead are excluded." | H |
| Sato et al. 2025 | Block-encoded PDE-constrained optimisation that avoids tomography; wave-equation material design example | Numerics | [arXiv:2511.14420](https://arxiv.org/abs/2511.14420) | Abstract: "avoid classical access to the full solution that requires quantum state tomography canceling out the potential quantum speedups" | H |
| Li, Jia, Wang, Duan 2026 | **Quantum-assisted acoustic FWI**: Born/adjoint/Gauss–Newton via Schrödingerised propagation, 9-qubit compiled instance, 2-qubit VQLS | Ideal-circuit sampling (no hardware stated) | [arXiv:2607.26880](https://arxiv.org/abs/2607.26880) | Abstract: "A compiled nine-qubit instance … Bernoulli samples from ideal-circuit probabilities drive a four-parameter hybrid inversion" | H |
| Nguyen, Vashisth, Tura 2026 | Hybrid quantum-classical PINN (PQC) for acoustic FWI; says it applies to medical ultrasound tomography | JAX statevector simulator only | [arXiv:2606.01110](https://arxiv.org/abs/2606.01110) | Abstract: "broadly applicable to wave-based inverse problems beyond geophysics, including medical ultrasound tomography" | H |
| Lively, Pagni, Camacho 2025 | *Quantum-inspired* tensor-network wave solver, 10¹³ grid points on a laptop (a classical competitor) | Classical | [arXiv:2504.11181](https://arxiv.org/abs/2504.11181) | Abstract | H |
| Quantum annealing for seismic inversion (Souza et al. 2022, *Front. Phys.* 9, 748285; others) | Linearised inversion as a QUBO | D-Wave | cited in Schade §1, §5.5 | "In all studies, the quantum resources are used to solve linearised inverse problems." | H |
| **Medical / transcranial ultrasound + quantum** | **No prior paper found** | — | Searches 2026-10-17: "quantum … ultrasound computed tomography / transcranial / skull" returned only classical work (e.g., BrainPuzzle [arXiv:2510.20029](https://arxiv.org/abs/2510.20029)) | This is absence of evidence, not proof. Say "to our knowledge" | L–M |

**Verdict on "first":**
- NOT defensible: "first quantum wave-equation simulation on IBM hardware", "first heterogeneous-media quantum wave simulation" (Schade 2024 did both), and "first quantum FWI" (2606.01110 and 2607.26880 exist, though both are simulator-only).
- Defensible with hedging: "To our knowledge, the first quantum Hamiltonian simulation of a *transcranial (scalp–skull–brain) acoustic layer model* on IBM hardware, *with Qiskit Runtime error mitigation*." Schade reported none.

---

## 4. Readout limits

| Claim | Number / Equation | Source | Exact quote / location | Conf. |
|---|---|---|---|---|
| Shot noise | Std error of a probability or expectation ∝ 1/√S. At 10⁴ shots that is ~1 %; at 10⁶ it is ~0.1 % | Schade §4 (same arXiv link) | "decreases up to prefactors with 1/√S, where S is the number of samples" | H |
| Amplitude estimation | \|ã − a\| ≤ 2πk√(a(1−a))/M + k²π²/M² with M oracle calls, so error ~1/M (Heisenberg) vs 1/√M | Brassard, Høyer, Mosca, Tapp, *AMS Contemp. Math.* 305:53–74 (2002), [arXiv:quant-ph/0005055](https://arxiv.org/abs/quant-ph/0005055) | Theorem 12 (Amplitude Estimation) | H |
| AE needs coherent depth | M sequential oracle calls. Not NISQ-friendly | same (circuit Fig. 1) | Inference from Theorem 12 structure | M |
| Aaronson's four HHL caveats | (1) load b fast; (2) apply e^{−iAt} fast; (3) κ small; (4) the output is a state \|x⟩, not x | S. Aaronson, "Read the fine print", *Nature Physics* **11**, 291–293 (2015), doi:10.1038/nphys3272. Preprint: [scottaaronson.com/papers/qml.pdf](https://www.scottaaronson.com/papers/qml.pdf) | Caveat (4): "learning the value of any specific entry xi will, in general, require repeating the algorithm roughly n times, which would once again kill the exponential speedup." | H |
| Same point for wave HS | QST is exponential in n | Schade §4/§5.2 | see §1 | H |
| Way out | Read scalar functionals (energy in a region, l2 misfit), not the whole field | Bösch 2025 Thm 2; Babbush 2023 | see §1b, §3 | H |

**Readout-wall arithmetic (ours, label as estimate):** a 3-D head grid of 85×10⁶ cells × ~10–12 recorded time slices gives ~10⁹ numbers. 10⁴ shots return at most 10⁴ bitstrings, i.e. ≤ 10⁴ × 29 bits ≈ 3×10⁵ bits. Holevo-type counting means you cannot read out 10⁹ reals; you can estimate O(1) scalars per batch of shots. Conf. **M**: the logic is standard, but the numbers are ours. The *field count* (cells × slices) is the team's figure; check that R1/R2 uses the same 85M.

---

## 5. IBM hardware facts (as of 2026-10-17)

| Claim | Number | Source | Exact quote / location | Conf. |
|---|---|---|---|---|
| Heron r2 size/topology | 156 qubits, heavy-hex | [IBM processor types](https://quantum.cloud.ibm.com/docs/en/guides/processor-types) | "r2 (July 2024) … 156 qubits in a heavy-hexagonal lattice … new TLS mitigation feature" | H |
| Heron r3 | Released July 2025; 156 qubits; improved coherence, gates, readout | same | "r3 (July 2025) Heron r3 is the result of targeted manufacturing improvements that directly impact coherence, gate fidelity, and readout performance." | H |
| Heron r1 | 133 qubits (Dec 2023) | same | "r1 (December 2023) The first version of Heron with 133 qubits." | H |
| Nighthawk r1 | 120 qubits, square grid (Dec 2025) | same | "r1 (December 2025) The first version of Nighthawk, with 120 qubits." | H |
| Nighthawk r2 | 120 programmable / 458 physical, fast reset (Sep 2026) | same | "120 programmable qubits and 458 physical qubits, including a high speed reset on each qubit" | H |
| Nighthawk couplers / depth | 218 tunable couplers (vs 176 on Heron); 5,000 2Q gates, 7,500 by end-2026, 10,000 in 2027 | [IBM newsroom, 12 Nov 2025](https://newsroom.ibm.com/2025-11-12-ibm-delivers-new-quantum-processors,-software,-and-algorithm-breakthroughs-on-path-to-advantage-and-fault-tolerance) | "120 qubits linked together with 218 next-generation tunable couplers"; "up to 5,000 two-qubit gates"; "up to 7,500 gates by the end of 2026 and then up to 10,000 gates in 2027" | H |
| Nighthawk T1 | median ~350 µs | [The Quantum Insider, 13 Jan 2026](https://thequantuminsider.com/2026/01/13/ibm-announces-nighthawk-and-latest-heron-are-now-available/), citing IBM release notes (that URL now 404s) | "median energy-relaxation time, known as T1, of roughly 350 microseconds" | M |
| **Live median 2Q (CZ) error, Heron r3** | ibm_boston 1.52e-3; ibm_aachen 1.51e-3; ibm_pittsburgh 1.58e-3 | [IBM Compute resources table](https://quantum.cloud.ibm.com/computers?view=table) (page JSON field `two_q_error_median`, fetched 2026-10-17) | Definition on page: "2Q error (median): The median two-qubit error rate from all edges measured by isolated randomized benchmarking." | H (snapshot; changes daily) |
| Live median 2Q error, Heron r2 | ibm_kingston 1.95e-3; ibm_fez 2.54e-3; ibm_marrakesh 2.80e-3 | same | same | H (snapshot) |
| Live best-pair 2Q error | ibm_boston 5.19e-4 (CZ on qubits 140–141) | same | "2Q error (best): The lowest two-qubit error rate from all edges" | H |
| Live EPLG (100-qubit chain) | boston 2.41e-3; kingston 3.52e-3; fez 4.14e-3; phoenix (Nighthawk r2) 3.50e-3 | same | "2Q error (layered): The average two-qubit error rate per layered gate (EPLG) for a 100-qubit chain." | H |
| Live readout error (median) | boston 3.5e-3; fez 1.0e-2; marrakesh 1.7e-2 | same | `readout_error_median` | H |
| CLOPS | Heron ~300–340K; Nighthawk r2 (ibm_phoenix) ~2.0M; Nighthawk r1 ~25K | same | `clops` | H |
| **Open Plan quota** | 10 min QPU time per rolling 28 days | [IBM plans overview](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview) | "Run your quantum circuits on the world's best QPUs for free (up to 10 minutes per 28-day rolling window)." | H |
| Starling | 2029; 200 logical qubits; 100M operations; Poughkeepsie | [IBM newsroom, 10 Jun 2025](https://newsroom.ibm.com/2025-06-10-IBM-Sets-the-Course-to-Build-Worlds-First-Large-Scale,-Fault-Tolerant-Quantum-Computer-at-New-IBM-Quantum-Data-Center) | "Delivered by 2029 … running 100 million quantum operations using 200 logical qubits" | H |
| Blue Jay | 2,000 logical qubits, 1B operations; roadmap slot 2033+ | same newsroom + [IBM roadmap 2033+](https://www.ibm.com/roadmaps/quantum/2033+) | "capable of executing 1 billion quantum operations over 2,000 logical qubits" | H (capability); M (2033 date, from the roadmap page via search) |
| Intermediate steps | Loon 2025, Kookaburra 2026, Cockatoo 2027 | same newsroom | "IBM Quantum Cockatoo, expected in 2027, will entangle two Kookaburra modules" | H |

**Correction:** the 156 count is Heron r2/r3, not Nighthawk. Nighthawk has 120 qubits. Do not quote "~5×10⁻⁴" as Heron r3's typical CZ error: that is the *best* pair. The *median* is ~1.5×10⁻³.

---

## 6. Error mitigation in Qiskit Runtime

| Technique | What it does | Primary citation | Current Qiskit docs | Exact quote | Conf. |
|---|---|---|---|---|---|
| ZNE | Run at amplified noise (gate folding), extrapolate to zero | Temme, Bravyi, Gambetta, *PRL* 119, 180509 (2017), [arXiv:1612.02058](https://arxiv.org/abs/1612.02058); demo: Kandala et al., *Nature* 567, 491 (2019), [arXiv:1805.04492](https://arxiv.org/abs/1805.04492) | [Techniques guide](https://quantum.cloud.ibm.com/docs/en/guides/error-mitigation-and-suppression-techniques); [ZneOptions](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-zne-options) | Docs: "it is not guaranteed to produce an unbiased result"; "default settings sample the expectation value at three noise factors, leading to a roughly 3x overhead" | H |
| PEA | Learns the twirled per-layer noise model, then amplifies it probabilistically for ZNE | Kim et al., "Evidence for the utility of quantum computing before fault tolerance", *Nature* **618**, 500–505 (2023), doi:10.1038/s41586-023-06096-3 (127 qubits). Noise model: van den Berg et al. [arXiv:2201.09866](https://arxiv.org/abs/2201.09866) | Techniques guide; `zne.amplifier="pea"` | "For utility-scale experiments, PEA is often the best choice. Because PEA is a ZNE noise amplification technique, you also need to enable ZNE." | H |
| Caveat on Kim 2023 | Classical simulations later reproduced it | Tindall et al., *PRX Quantum* 5, 010308 (2024), [arXiv:2306.14887](https://arxiv.org/abs/2306.14887); Begušić & Chan [arXiv:2306.16372](https://arxiv.org/abs/2306.16372) | — | "Our classical simulations on a single core of a laptop are orders of magnitude faster…" (Begušić) | H |
| TREX | Twirled readout; diagonalises the readout-error matrix | van den Berg, Minev, Temme, *PRA* **105**, 032620 (2022), [arXiv:2012.09738](https://arxiv.org/abs/2012.09738) | Techniques guide; `resilience.measure_mitigation` | "measurement twirling has the effect of diagonalizing the readout-error transfer matrix, making it easy to invert" | H |
| Pauli twirling | Turns coherent noise into Pauli noise | Wallman & Emerson, *PRA* 94, 052325 (2016), [arXiv:1512.01098](https://arxiv.org/abs/1512.01098) | [TwirlingOptions](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-twirling-options) | "enable_gates … Whether to apply 2-qubit Clifford gate twirling. Default: For the Sampler: False" | H |
| Dynamical decoupling | Pulse sequences on idle qubits | Viola & Lloyd, *PRA* 58, 2733 (1998), [arXiv:quant-ph/9803057](https://arxiv.org/abs/quant-ph/9803057) | [DynamicalDecouplingOptions](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-dynamical-decoupling-options) | `sequence_type` ∈ {'XX','XpXm','XY4'}, default "XX", default enable False. Guide: DD "might not improve performance" on densely packed circuits | H |
| PEC | Unbiased, but overhead γ² grows exponentially with depth | Temme 2017; van den Berg 2022 | Techniques guide; `pec_mitigation` | "It scales quadratically with γ, which in turn scales exponentially with the depth of the circuit." | H |
| Estimator resilience levels | 0 = none; 1 = readout (TREX + measure twirling); 2 = + ZNE + gate twirling. Default 1 | [EstimatorOptions](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-estimator-options), [ResilienceOptionsV2](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-resilience-options-v2) | — | "zne_mitigation … False for resilience levels 0 and 1, and True for resilience level 2" | H |
| SamplerV2 | Has twirling + DD only. **No ZNE/TREX/PEA** (those are Estimator-only) | [SamplerOptions](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-sampler-options) | Options list: dynamical_decoupling, twirling, default_shots (default 4096) | H |
| **API change warning** | New client-side Estimator in qiskit-ibm-runtime ≥ 0.50.0: PEA/PEC need a *separate noise-learning job*. A new "directed execution model" is in beta | Techniques guide | "If you are using the new client-side Estimator introduced in qiskit-ibm-runtime v0.50.0, a separate noise-learning job is required to use PEA." | H |

**Implication for Aperion:** to show "noise vs mitigation", use **EstimatorV2** with observables such as ⟨Z_i⟩ or the projector onto a skull/brain cell, at resilience 0/1/2 and with PEA. SamplerV2 counts cannot be mitigated by ZNE/TREX in Runtime. PEA learning costs QPU time, which matters on a 10-min Open Plan.

---

## 7. "Options considered" table citations (slide 10)

| Option | What it solves | Why not (for us) | Citation | Quote / location | Conf. |
|---|---|---|---|---|---|
| Quantum annealing (D-Wave) | Ising/QUBO minimisation (combinatorial optimisation), heuristic | Our forward problem is linear time evolution, not optimisation. Prior seismic use was linearised inversion only | Kadowaki & Nishimori, *PRE* 58, 5355 (1998), [arXiv:cond-mat/9804280](https://arxiv.org/abs/cond-mat/9804280); [D-Wave QPU intro](https://docs.dwavesys.com/docs/latest/c_qpu_intro.html) | D-Wave: QPU "can be viewed as a heuristic that minimizes Ising objective functions using a physically realized version of quantum annealing" | H (D-Wave quote via search snippet: M) |
| QAOA | Approximate combinatorial optimisation | Same mismatch | Farhi, Goldstone, Gutmann, [arXiv:1411.4028](https://arxiv.org/abs/1411.4028) (2014) | "produces approximate solutions for combinatorial optimization problems" | H |
| VQE | Ground-state eigenvalues via variational circuits | Wave propagation is dynamics, not a ground state; barren plateaus | Peruzzo et al., *Nat. Commun.* 5, 4213 (2014), [arXiv:1304.3061](https://arxiv.org/abs/1304.3061) | Title: "A variational eigenvalue solver on a photonic quantum processor" | H |
| Quantum kernels / QML | Classification via quantum feature maps | Benchmarks: classical baselines win | Havlíček et al., *Nature* 567, 209 (2019), [arXiv:1804.11326](https://arxiv.org/abs/1804.11326); caveat: Bowles, Ahmed, Schuld 2024, [arXiv:2403.07059](https://arxiv.org/abs/2403.07059) | Bowles: "out-of-the-box classical machine learning models outperform the quantum classifiers" | H |
| HHL (linear systems) | Prepares \|x⟩ for Ax = b in poly(log N, κ) | Four caveats; output is a state | Harrow, Hassidim, Lloyd, *PRL* 103, 150502 (2009), [arXiv:0811.3171](https://arxiv.org/abs/0811.3171); Aaronson 2015 | see §4 | H |
| **Hamiltonian simulation (chosen)** | Unitary e^{−iHt}; native fit for lossless waves | Needs FT for scale; attenuation is non-unitary | Lloyd, "Universal Quantum Simulators", *Science* 273, 1073 (1996), doi:10.1126/science.273.5278.1073; Trotter, *Proc. AMS* 10, 545 (1959); Suzuki, *J. Math. Phys.* 32, 400 (1991); Childs et al., "A Theory of Trotter Error", *PRX* 11, 011020 (2021), [arXiv:1912.08854](https://arxiv.org/abs/1912.08854) | Schade §5.4 on unitarity | H |

---

## 8. Resource estimate for the 3-D head (85M cells)

| Item | Number | Basis | Source | Conf. |
|---|---|---|---|---|
| Data qubits (Costa encoding) | ⌈log₂((1+D)·N)⌉ = ⌈log₂(4 × 8.5×10⁷)⌉ = ⌈28.3⌉ = **29** | Costa qubit formula, D = 3 | [arXiv:1711.05394](https://arxiv.org/abs/1711.05394) §2 | H (formula), M (our arithmetic) |
| Plus ancillas / oracle registers | Tens to hundreds more | Suau Fig. 2 fit "11 + 3 log₂x" logical qubits | [arXiv:2003.12458](https://arxiv.org/abs/2003.12458) Fig. 2 | M |
| Grid per side | 85×10⁶^{1/3} ≈ 440 | arithmetic | — | M |
| Query complexity scale | τ = s‖H‖max t, s = 2D = 6; t ∝ crossing time ≈ 440 cells × (c_max/c_min); qubitization O(τ + log 1/ε) | Costa eq. (10); Schade App. B | both | H (formula); L (numbers) |
| Practical speedup ceiling | ≤ quartic (3-D) vs classical FD | Bösch 2025 §III | [arXiv:2411.17630](https://arxiv.org/abs/2411.17630) | H |
| Explicit Trotter CNOT scaling (homogeneous 3-D elastic) | 1st order O((log N)³ T² v²/(h² ε)); 2nd order O((log N)^{7/2} T^{3/2} v^{3/2}/(h^{3/2} ε^{1/2})) | Table I | [arXiv:2604.20284](https://arxiv.org/abs/2604.20284) | H |
| Empirical gate fit (1-D, oracle-based) | ≈ λ N_d^{3/2} log₂²N_d, λ ≈ 3×10⁵. Plugging in N_d = 8.5×10⁷ gives ~10²⁰ gates. **Illustration only**: this is 1-D, older circuits, k = 1 | Suau Fig. 4a | [arXiv:2003.12458](https://arxiv.org/abs/2003.12458) | L (extrapolation) |
| Compare to Starling budget | 10⁸ ops / 200 logical qubits | IBM newsroom | §5 | H |
| Honest bottom line | 29 data qubits fits Starling easily. Gate count per run is likely ≥ 10⁸ once heterogeneous-media oracles and ε are included, and FWI needs many runs × many shots. **Treat as post-2029 / Blue Jay-class** | Our synthesis | — | L |

Recommended slide wording: "Memory scales as log₂: 29 logical data qubits for 85M cells (Costa 2019). Time scales at best quartically better than classical (Bösch 2025). Gate counts for heterogeneous 3-D media have not yet been published. Our estimate is ≥10⁸ gates, at or beyond Starling's 10⁸-op budget."

---

## Slide mapping

**Slide 9 – Why the problem is quantum-shaped**
- Classical: ρ ∂tt u = ∂x(µ ∂x u) (Schade eq. 11) → M ü = Ku.
- Quantum: **i ∂t|ϕ⟩ = H|ϕ⟩, H = i[[0, U],[−Uᵀ, 0]], U = E^{1/2} D M^{-1/2}** (Schade eqs. 19, 22, 25). Equivalent graph form: **H = (1/a)[[0, B],[B†, 0]], BB† = L** (Costa eq. 4).
- One-liner: "Lossless waves conserve energy, so their evolution is unitary, which is exactly what a quantum computer does." The caveat goes on the same slide: attenuation is not unitary (Schade §5.4).

**Slide 10 – Options table:** one row each from §7. QA → Kadowaki–Nishimori 1998 + D-Wave docs; QAOA → Farhi 2014; VQE → Peruzzo 2014; kernels → Havlíček 2019 + Bowles 2024; HHL → HHL 2009 + Aaronson 2015; HS → Lloyd 1996 (+ Trotter/Suzuki).

**Slide 12 – Two encodings (7 cells: scalp, skull, skull, brain, skull, skull, scalp)**
- **Compact (binary/amplitude): 4 qubits.** 7 vertices + 8 edges (6 internal + 2 Dirichlet boundary) = 15 amplitudes, padded to 2⁴ = 16. Matches Schade App. C ("2^{n−1} − 1 grid points for n qubits": 7 points ↔ n = 4) and Costa (dim = |V|+|E|).
  - Cost: H becomes a dense sum of multi-qubit Pauli strings, so many CNOTs on heavy-hex. Schade needed ~870 gates for one time point.
  - Note: Schade's text says "5 qubits" for this case. Cite it as "4–5 qubits".
- **One-per-site (unary / one-hot): 15 qubits.** One qubit per vertex and per edge, restricted to the single-excitation subspace. Each nonzero H_jk becomes a nearest-neighbour XX+YY-type hopping term, so you get a *local* 1-D chain that maps onto heavy-hex with few SWAPs, and each Trotter step is shallow. The trade-off is linear rather than logarithmic qubits.
  - Encoding-tradeoff citation: Sawaya et al., *npj QI* 6, 49 (2020), [arXiv:1909.12847](https://arxiv.org/abs/1909.12847), which compares unary/Gray/binary encodings under Trotterization.
  - The specific "single-excitation XY chain" construction is our derivation (Conf. M). Verify the Pauli form with `SparsePauliOp.from_operator` before the slide goes final.

**Slide 16 – Hardware results + mitigation**
- Prior art baseline: Schade on Brisbane gave RL2 up to 60 %, with no mitigation, exact-unitary compilation, and QST at 1000 shots.
- Our plan: Heron r3 (median CZ ~1.5e-3, readout ~0.35–0.55 %) with EstimatorV2 at resilience 0 → 1 (TREX) → 2 (ZNE + gate twirling) → PEA, plus DD. Show the bar chart.
- Do not claim "utility" by analogy to Kim 2023 without the Tindall/Begušić caveat.
- Budget: 10 min / 28 days on Open Plan. PEA noise learning eats into it.

**Slide 17 – 1-D vs 3-D resources + roadmap**
- 7 cells: 4 or 15 qubits.
- 85M cells: 29 data qubits (Costa), polynomial-only speedup ≤ quartic (Bösch 2025).
- Gates: unknown for heterogeneous 3-D. Our estimate is ≥10⁸, labelled as an estimate.
- Timeline: Heron r3 (2025) → Nighthawk 120q, 5k→7.5k→10k 2Q gates (2025–27) → Starling 2029 (200 LQ, 10⁸ ops) → Blue Jay 2033+ (2,000 LQ, 10⁹ ops).

**Slide 18 – Readout wall**
- 10⁹ field values vs 10⁴ shots. Each shot is one bitstring of ~29 bits, and per-value error is ∝ 1/√S (Schade §4).
- Full tomography "nullif[ies] any speedup" (Schade §4). HHL caveat 4 (Aaronson 2015): reading x_i "would once again kill the exponential speedup".
- Escape route: compute the misfit *on the QPU* (Bösch 2025 Thm 2, O(1/ε) calls with amplitude estimation, BHMT Thm 12) or use block-encoded optimisation (Sato 2025).

**Slide 20 – Innovation vs prior work**
- Prior work: Costa 2019 (algorithm), Suau 2021 (resources), Schade 2024 (heterogeneous 1-D on IBM Brisbane), Wright 2024 (Quantinuum H1-1), Bösch 2025 (sources, loss, quartic), 2026 quantum-FWI preprints (2606.01110, 2607.26880, simulator-only).
- Our delta: a *medical* layered scalp/skull/brain model; Qiskit Runtime mitigation (none in Schade); a comparison of two encodings on Heron; an honest readout analysis.
- Wording: "to our knowledge, first transcranial-ultrasound-motivated…".

---

## Graphs & images

| # | Graph / image | Data source | How to make | Slide |
|---|---|---|---|---|
| 1 | Circuit for one Trotter step (one-per-site: a brick of XX+YY gates on the 15-qubit chain; compact: Pauli-string exponentials) | Our Qiskit circuit; reference figure Wright 2024 Fig. 1 (n+1 = 4 qubit wave circuit), [arXiv:2402.19247](https://arxiv.org/abs/2402.19247) | `qc.draw('mpl')` on a single step, before and after transpilation (show the CZ count) | 12 |
| 2 | Wavefield snapshots: classical vs ideal vs hardware (3 panels at t₁, t₂, t₃ over the 7 cells) | Ours. Style reference: Schade Fig. 2 | Line plot; colour cell background by tissue | 16 |
| 3 | Fidelity / RL2 vs circuit depth (number of Trotter steps), per encoding | Ours. Expectation anchor: Schade 0.999^870 ≈ 0.42; Wright Fig. 3 (optimal qubit count from algorithmic vs gate error) | Line chart, log-x | 16 |
| 4 | Noise vs mitigation bar chart: \|⟨O⟩_hw − ⟨O⟩_exact\| for resilience 0/1/2/PEA, ± stds from Estimator | Ours (EstimatorV2 `evs`, `stds`) | Grouped bars with error bars | 16 |
| 5 | 1-D → 3-D resource scaling: qubits (log₂, Costa) vs classical memory (linear); plus speedup exponent bars (2×/3×/4× polynomial, Bösch) | Costa §2; Bösch §III | Log-log line, N from 7 to 8.5e7 | 17 |
| 6 | IBM roadmap timeline: Heron r2 2024, r3 2025, Nighthawk 2025–26, Loon 2025, Kookaburra 2026, Cockatoo 2027, Starling 2029, Blue Jay 2033+ | IBM newsroom (Jun & Nov 2025), processor-types page, roadmap page | Horizontal timeline. Mark "our 3-D estimate ≥10⁸ gates" against Starling's 10⁸ | 17 |
| 7 | Readout wall: bar on log axis showing 10⁹ (field values) vs 10⁴ (shots) vs 6×10² s (Open Plan seconds / 28 d) | Our arithmetic; Schade §4; IBM plans page | Log-scale bars | 18 |
| 8 | Prior-work map: 2×2 grid (theory ↔ hardware; homogeneous ↔ heterogeneous/medical), with Aperion in its corner | §3 table | Scatter / quadrant | 20 |
| 9 | Live hardware card: median CZ, readout, EPLG for the QPU actually used, with timestamp | [IBM computers table](https://quantum.cloud.ibm.com/computers?view=table) on run day | Small table | 16 |

---

## Things in the team's brief that are wrong or need rewording

1. **"Schade … Trotterization … ran on IBM Brisbane"**: no Trotterization ran on hardware. They compiled the *exact* matrix exponential (scaling-and-squaring via PauliEvolutionGate, ~870 gates). Trotter and qubitization appear only in the complexity analysis.
2. **"Exponential speedup"** for the wave equation: the same group (Bösch et al. 2025) says the practical speedup is polynomial, quartic in 3-D at best. Schade's "exponential" assumes oracle access and ignores travel-time scaling and readout.
3. **"First"**: Schade already ran a heterogeneous 1-D wave equation on IBM hardware, and quantum-FWI preprints exist (simulator-only). Only the "transcranial/medical + mitigation" framing holds up, and only with a "to our knowledge" hedge.
4. **Heron error rate**: ~5e-4 is the *best* pair. The median CZ on Heron r3 is ~1.5e-3, and on Heron r2 ~2–2.8e-3 (snapshot 2026-10-17). Nighthawk is 120 qubits, not 156.
5. **Schade qubit count**: the paper says "5 qubits" in the text, but its own formula gives 4 for 7 grid points. Cite "4–5".
6. **Costa H**: include the 1/a prefactor. For real B, B† = Bᵀ. The edge register is auxiliary, and the vertex-subspace probability can be arbitrarily small (§10).
7. **SamplerV2 cannot do ZNE/TREX/PEA**: those are EstimatorV2 resilience options. qiskit-ibm-runtime ≥ 0.50 needs a separate noise-learning job for PEA.
8. **IBM Brisbane** was retired 2025-11-03, so we cannot rerun Schade's exact hardware.
