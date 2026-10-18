# Limitations (what our results can and cannot support)

## Physics simplifications
- **Validated against Stride only in 2D, at one frequency, on a small 5 cm slice.** Agreement is 0.993 correlation;
  the ≈7% residual comes from different source/receiver implementations.
- **The original Costa et al. graph form encodes a different medium** (density ∝ 1/c²; 0.76 correlation with the
  paper's physics). Our default `form="paper"` coupling fixes this; the old form stays available as `form="graph"`.
- **No absorption.** Unitary quantum evolution conserves energy. Real skull absorbs and scatters ultrasound, which
  the paper says matters. Non-unitary extensions exist ("Schrodingerisation"), but they add qubits and gates; not done here.
- **Closed box.** Boundaries are fixed zero-pressure (reflecting) instead of absorbing, because absorbing
  boundaries are also non-unitary. The classical FWI baseline (notebook 05) does use absorbing sponges.
- **Observable.** The quantum read-out is *wave energy* at a cell, not the pressure trace a transducer records.
- **Constant density, acoustic only.** No shear waves or mode conversion in bone.
- **Toy resolution.** Quantum runs use 7-cell lines and 3³–7³ heads, against the paper's 440³ cells.
  At 7³ the skull is a cell or two thick.
- **Classical FWI is 2D** (laptop). The paper stresses 3D is essential; the same code runs in 3D on a GPU node.

## Quantum caveats
- Everything we ran is **classically simulable**, by construction. The unary encoding stays in a one-excitation
  subspace (we replay it classically in `qwave/subspace.py`), and the compact encodings are small.
  We claim no proven complexity-theoretic quantum advantage. The projected speed-up in `scaling/crossover.py` comes
  from the QPU applying every gate in a layer at once, measured on IBM Heron gate times, and is a projection for
  larger, lower-noise hardware than exists today.
- Compact-encoding gate counts use generic Pauli-Trotter circuits. Structured block-encodings from the literature
  would be far cheaper asymptotically; we did not implement them. The 3D compact count is an *estimate* from
  Pauli weights, not a compiled circuit.
- The 3D gate count is a lower bound (steps scaled linearly from an 11³ grid), not a measured or fitted value.
- Noise results come from IBM's *FakeKingston* noise model unless a real-hardware JSON is present in `results/`.
  Models miss drift and crosstalk.
- Zero-noise extrapolation uses only two noise scales and is not guaranteed unbiased. Post-selection discards shots.
- Hybrid demo: the "measured" data are exact classical energies of the true head, and quantum shots are ideal
  (noise-free sampling). Real data would add noise and model error.

## Clinical caveats
- The phantom is a layered ellipsoid, not anatomy (the paper uses the MIDA head model).
- No patient data, no validation, no regulatory pathway. Detecting a 2%-contrast single-cell bleed is a toy target.
