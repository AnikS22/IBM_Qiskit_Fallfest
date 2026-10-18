# Use case: a portable brain scan for the first hour of a stroke

## The problem
Clot strokes and bleeding strokes need opposite treatment: the clot-busting drug that saves one kind of patient
is dangerous for the other. So no one can be treated until the brain is imaged, and CT/MRI scanners are large
machines that stay in the hospital. Guasch et al. (2020) report that relatively few stroke patients get any brain
scan within the critical first hour.

## Who it affects
- **Patients** with suspected stroke, head trauma, or bleeding in the brain.
- **Paramedics and emergency physicians**, who must decide treatment and destination without imaging.
- **Neurologists and stroke teams**, whose treatment window closes minute by minute.
- **Health systems in low-resource or remote settings**, where CT/MRI may not exist at all.

## The proposed technology
A helmet of 1,024 ultrasound transducers plus *full-waveform inversion* (FWI), a reconstruction method from
geophysics (Guasch et al., npj Digital Medicine 3:28, 2020). FWI repeatedly simulates sound travelling through a
guessed head and adjusts the guess until simulated and recorded signals match. In simulation it gives sub-millimetre
3D images through the skull and recovers a haemorrhage. Its bottleneck is compute: ~32 h on 128 CPU nodes for one
3D image, with the authors targeting <10 min on GPUs.

## Where quantum computing could fit, and what we tested
The expensive step, simulating the sound wave, is a linear energy-conserving system that can be rewritten as
quantum (Hamiltonian) evolution (Costa, Jordan & Ostrander 2019). In the compact encoding, the paper's
85-million-cell head fits in about **29 qubits**. We built that mapping in Qiskit for 1D, 2D and 3D heads,
verified it against classical solvers, ran noise analysis, and estimated what the full problem needs.

## What it would take to be real
- Fault-tolerant quantum hardware able to run the compact encoding with structured, block-encoded circuits.
  Generic circuits need about 10⁶ two-qubit gates even for a 3×3×3 head.
- A way around the **read-out wall**. FWI needs about 10⁹ numbers per iteration; sampling them costs about 10¹³ shots.
  Quantum only helps if the clinical question can be reduced to very few numbers (e.g., one misfit, or bleed yes/no).
- More, cheaper, lower-noise qubits. Our accuracy-matched benchmark (`scaling/crossover.py`) projects the quantum
  forward solver overtaking our classical solver at ~283³ voxels and running ~3.3× faster at the full 440³ head.

**Roadmap:** run reconstruction on classical hardware today, with the quantum forward solver validated on real IBM
hardware (done: `ibm_marrakesh`, job `db9smd9gv2cc73e60pm0`). As quantum hardware grows and gets cheaper, move the
wave-simulation step onto the QPU, and design the clinical question around few-number outputs (bleed yes/no).
