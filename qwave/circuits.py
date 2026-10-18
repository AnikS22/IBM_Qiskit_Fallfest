"""Qiskit circuits and simulators for both encodings."""
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit.synthesis import SuzukiTrotter

from .encoding import compact_pauli_op, compact_qubits, unary_layers, unary_qubits

BASIS = ["cz", "rz", "sx", "x"]


def compact_circuit(grid, c, t, steps, source=0, op=None):
    """Compact (binary-index) circuit: X gates load `source` as a bit pattern, then 2nd-order Suzuki-Trotter exp(-iHt) with `steps` reps."""
    op = compact_pauli_op(grid, c) if op is None else op
    n = op.num_qubits
    qc = QuantumCircuit(n, name="compact_wave")
    for q in range(n):
        if (source >> q) & 1:
            qc.x(q)
    qc.append(PauliEvolutionGate(op, time=t, synthesis=SuzukiTrotter(order=2, reps=steps)), range(n))
    return qc


def unary_circuit(grid, c, t, steps, source=0, layers=None):
    """Second-order (Strang) Trotter over the bond layers. source = vertex index (qubit index = site index)."""
    layers = unary_layers(grid, c) if layers is None else layers
    nq = unary_qubits(grid)
    qc = QuantumCircuit(nq, name="unary_wave")
    qc.x(source)
    dt = t / steps
    seq = [(L, dt / 2) for L in layers[:-1]] + [(layers[-1], dt)] + [(L, dt / 2) for L in reversed(layers[:-1])]
    for _ in range(steps):
        for L, tau in seq:
            qc.append(PauliEvolutionGate(L, time=tau), range(nq))
    return qc


def gate_cost(qc, opt=1):
    """Transpile to the {cz, rz, sx, x} basis; returns CZ count, depth and qubit count."""
    tq = transpile(qc, basis_gates=BASIS, optimization_level=opt)
    return {"cz": int(tq.count_ops().get("cz", 0)), "depth": int(tq.depth()), "qubits": tq.num_qubits}


def compact_receiver_probs(qc, receivers):
    """Noiseless statevector of the *decomposed* circuit (so Trotter error is real)."""
    tq = transpile(qc, basis_gates=BASIS, optimization_level=0)
    p = Statevector(tq).probabilities()
    return p[np.asarray(receivers)]


def unary_receiver_probs(qc, receivers):
    """P(excitation on receiver qubit) = (1 - <Z_r>)/2, computed exactly with the MPS simulator."""
    from qiskit_aer import AerSimulator
    tq = transpile(qc, basis_gates=BASIS, optimization_level=0)
    nq = tq.num_qubits
    for r in receivers:
        z = ["I"] * nq; z[nq - 1 - r] = "Z"
        tq.save_expectation_value(SparsePauliOp("".join(z)), range(nq), label=f"z{r}")
    method = "statevector" if nq <= 22 else "matrix_product_state"
    res = AerSimulator(method=method).run(tq).result().data()
    return np.array([(1 - res[f"z{r}"].real) / 2 for r in receivers])


def compact_cz_estimate(op, steps):
    """CZ count of a 2nd-order Trotter circuit without compiling it: each Pauli rotation of weight w
    costs ~2(w-1) CZ with a CNOT-ladder; 2nd order applies each term twice per step (minus merges)."""
    w = np.array([np.count_nonzero(p.x | p.z) for p in op.paulis])
    per_pass = int(np.sum(2 * np.maximum(w - 1, 0)))
    return 2 * per_pass * steps
