"""The quantum circuits reproduce the classical wave, in 1D, 2D and 3D."""
import numpy as np
import pytest
from qwave import Grid, head_phantom
from qwave.classical import exact_receiver_energy
from qwave.encoding import wave_hamiltonian, unary_full_op, unary_qubits
from qwave.circuits import compact_circuit, compact_receiver_probs, unary_circuit, unary_receiver_probs
from qwave.subspace import trotter_receiver_energy


def _problem(shape):
    g = Grid(shape); c, _ = head_phantom(shape); c = c.ravel()
    src = g.index(*([0] + [s // 2 for s in shape[1:]]))
    rx = [g.index(*([shape[0] - 1] + [s // 2 for s in shape[1:]])), g.index(*[s // 2 for s in shape])]
    return g, c, src, rx


@pytest.mark.parametrize("shape", [(7,), (2, 2)])
def test_unary_hamiltonian_equals_wave_hamiltonian_in_subspace(shape):
    g = Grid(shape); c = np.linspace(1.0, 1.9, g.n_vertices)   # arbitrary heterogeneous speeds
    M = unary_full_op(g, c).to_matrix(sparse=True).tocsr()
    idx = [1 << k for k in range(unary_qubits(g))]
    assert abs(M[idx][:, idx] - wave_hamiltonian(g, c)).max() < 1e-12


@pytest.mark.parametrize("shape,steps,tol", [((7,), 8, 2e-2), ((3, 3), 8, 2e-3)])
def test_compact_circuit_matches_classical(shape, steps, tol):
    g, c, src, rx = _problem(shape)
    ex = exact_receiver_energy(g, c, [1.5], src, rx)[0]
    p = compact_receiver_probs(compact_circuit(g, c, 1.5, steps, src), rx)
    assert np.abs(p - ex).max() < tol


@pytest.mark.parametrize("shape,steps,tol", [((7,), 8, 1e-2), ((3, 3), 8, 5e-3), ((3, 3, 3), 8, 1e-2)])
def test_unary_circuit_matches_classical(shape, steps, tol):
    g, c, src, rx = _problem(shape)
    ex = exact_receiver_energy(g, c, [1.5], src, rx)[0]
    p = unary_receiver_probs(unary_circuit(g, c, 1.5, steps, src), rx)
    assert np.abs(p - ex).max() < tol


@pytest.mark.parametrize("shape", [(7,), (3, 3), (3, 3, 3)])
def test_subspace_replay_equals_circuit(shape):
    g, c, src, rx = _problem(shape)
    a = trotter_receiver_energy(g, c, 1.5, 4, src, rx)
    b = unary_receiver_probs(unary_circuit(g, c, 1.5, 4, src), rx)
    assert np.abs(a - b).max() < 1e-9


def test_trotter_error_shrinks_with_steps():
    g, c, src, rx = _problem((5, 5, 5))
    ex = exact_receiver_energy(g, c, [2.0], src, rx)[0]
    errs = [np.abs(trotter_receiver_energy(g, c, 2.0, s, src, rx) - ex).max() for s in (4, 8, 16, 32)]
    assert all(e2 < e1 for e1, e2 in zip(errs, errs[1:])) and errs[-1] < 1e-3
