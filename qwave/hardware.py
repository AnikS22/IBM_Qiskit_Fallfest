"""Hardware experiment: the ear-to-ear ray through the 3D phantom, run as a 1D unary circuit.

Modes
  'ideal' : noiseless Aer
  'fake'  : Aer with the calibrated noise model of a real IBM device (FakeKingston) -- free, local
  'ibm'   : real IBM hardware via qiskit-ibm-runtime (uses QPU minutes; token read at run time, never stored)
"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager

from .grid import Grid
from .phantom import head_phantom, ray_through
from .encoding import unary_layers
from .circuits import unary_circuit


def ray_problem(shape3d=(7, 7, 7), bleed=False):
    """1D sound-speed line through the centre of the 3D phantom (bleed, if any, at the centre cell)."""
    centre = tuple(s // 2 for s in shape3d)
    c3, lab3 = head_phantom(shape3d, bleed=centre if bleed else None)
    c1 = ray_through(c3, axis=0); lab1 = ray_through(lab3, axis=0)
    return Grid((len(c1),)), c1, lab1


def fold(qc, factor):
    """Unitary folding for zero-noise extrapolation: U -> U (U^dag U)^k, factor = 2k+1."""
    assert factor % 2 == 1
    base = qc.remove_final_measurements(inplace=False)
    out = base.copy()
    for _ in range((factor - 1) // 2):            # barriers stop the transpiler cancelling U^dag U
        out.barrier(); out.compose(base.inverse(), inplace=True)
        out.barrier(); out.compose(base, inplace=True)
    out.measure_all()
    return out


def build_circuits(t=1.5, steps_list=(2, 4, 6, 8), shape3d=(7, 7, 7), folds=(1,), source=0):
    """Measured unary circuits for the healthy and bleed rays at each Trotter step count and fold factor.
    Returns (circuits, meta) with meta = {bleed, steps, fold} per circuit."""
    circs, meta = [], []
    for bleed in (False, True):
        g, c, lab = ray_problem(shape3d, bleed)
        layers = unary_layers(g, c)
        for steps in steps_list:
            qc = unary_circuit(g, c, t, steps, source, layers)
            qc.measure_all()
            for f in folds:
                circs.append(fold(qc, f) if f > 1 else qc)
                meta.append({"bleed": bleed, "steps": steps, "fold": f})
    return circs, meta


def analyse_counts(counts, receiver_qubit, n_qubits):
    """Raw and post-selected receiver energy from one circuit's counts.
    Post-selection keeps only shots with exactly one excitation. Standard errors are binomial."""
    tot = sum(counts.values())
    target = format(1 << receiver_qubit, f"0{n_qubits}b")
    w1 = {k: v for k, v in counts.items() if k.count("1") == 1}
    kept = sum(w1.values())
    raw = counts.get(target, 0) / tot
    post = (w1.get(target, 0) / kept) if kept else float("nan")
    return {"raw": raw, "raw_se": float(np.sqrt(raw * (1 - raw) / tot)),
            "postselected": post, "post_se": float(np.sqrt(post * (1 - post) / kept)) if kept else float("nan"),
            "kept_fraction": kept / tot, "shots": tot}


def run(circs, mode="fake", shots=4000, backend_name=None, dd=True, twirl=True, seed=7):
    """Returns list of counts dicts. 'ibm' mode needs an IBM Quantum API key (asked for at run time)."""
    if mode == "ideal":
        from qiskit_aer import AerSimulator
        sim = AerSimulator(method="matrix_product_state")
        from qiskit import transpile
        tc = transpile(circs, sim, optimization_level=1)
        res = sim.run(tc, shots=shots, seed_simulator=seed).result()
        return [res.get_counts(i) for i in range(len(circs))], None
    if mode == "fake":
        from qiskit_ibm_runtime.fake_provider import FakeKingston
        backend = FakeKingston()
    elif mode == "ibm":
        import getpass
        from qiskit_ibm_runtime import QiskitRuntimeService
        service = QiskitRuntimeService(channel="ibm_quantum_platform",
                                       token=getpass.getpass("IBM Quantum API key (not stored): "))
        backend = service.backend(backend_name) if backend_name else service.least_busy(operational=True, simulator=False)
    else:
        raise ValueError(mode)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend, seed_transpiler=seed)
    isa = pm.run(circs)
    if mode == "fake":
        from qiskit_aer import AerSimulator
        sim = AerSimulator.from_backend(backend)
        res = sim.run(isa, shots=shots, seed_simulator=seed).result()
        return [res.get_counts(i) for i in range(len(isa))], isa
    from qiskit_ibm_runtime import SamplerV2, Batch
    with Batch(backend=backend) as batch:
        sampler = SamplerV2(mode=batch)
        sampler.options.default_shots = shots
        sampler.options.dynamical_decoupling.enable = dd
        sampler.options.twirling.enable_gates = twirl
        sampler.options.twirling.enable_measure = twirl
        job = sampler.run(isa)
        print("job id:", job.job_id())
        result = job.result()
    return [r.join_data().get_counts() for r in result], isa
