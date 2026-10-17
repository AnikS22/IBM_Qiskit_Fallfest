"""The classical wave model is right: energy is conserved and two independent solvers agree, in 1D/2D/3D."""
import numpy as np
import pytest
from qwave import Grid, head_phantom
from qwave.classical import fd_receiver_energy, exact_receiver_energy, total_energy_fd
from qwave.encoding import wave_hamiltonian

SHAPES = [(7,), (5, 5), (5, 5, 5)]


@pytest.mark.parametrize("shape", SHAPES)
def test_grid_counts(shape):
    g = Grid(shape)
    nd = len(shape)
    assert g.n_vertices == np.prod(shape)
    assert g.n_edges == sum(np.prod(shape) // shape[a] * (shape[a] + 1) for a in range(nd))
    B = g.incidence()
    assert np.allclose(np.abs(B).sum(axis=0), np.where((g.edge_u >= 0) & (g.edge_v >= 0), 2, 1))


@pytest.mark.parametrize("shape", SHAPES)
def test_hamiltonian_hermitian(shape):
    g = Grid(shape); c, _ = head_phantom(shape)
    H = wave_hamiltonian(g, c.ravel())
    assert abs(H - H.conj().T).max() < 1e-12


@pytest.mark.parametrize("shape", SHAPES)
def test_energy_conserved(shape):
    g = Grid(shape); c, _ = head_phantom(shape)
    assert abs(total_energy_fd(g, c.ravel(), 3.0, 0) - 1.0) < 1e-3


@pytest.mark.parametrize("shape", SHAPES)
def test_exact_matches_finite_difference(shape):
    g = Grid(shape); c, _ = head_phantom(shape, bleed=tuple(s // 2 for s in shape)); c = c.ravel()
    src = 0; rx = [g.n_vertices - 1, g.n_vertices // 2]
    ts = np.linspace(0, 3, 7)
    assert np.abs(exact_receiver_energy(g, c, ts, src, rx) - fd_receiver_energy(g, c, ts, src, rx)).max() < 1e-4


def test_phantom_has_all_layers_3d():
    _, lab = head_phantom((7, 7, 7), bleed=(3, 3, 3))
    assert set(np.unique(lab)) == {0, 1, 2, 3, 4}


@pytest.mark.parametrize("shape", SHAPES)
def test_paper_form_is_the_papers_equation(shape):
    """Quantum coupling with form='paper' reproduces p_tt = c^2 * laplacian(p) (5/7-point stencil, Dirichlet)."""
    import scipy.sparse as sp
    from qwave.encoding import coupling
    g = Grid(shape); c, _ = head_phantom(shape, bleed=tuple(s // 2 for s in shape)); c = c.ravel()
    K = coupling(g, c, "paper")
    # discrete -laplacian with zero ghost cells: 2*ndim on the diagonal, -1 for each neighbour
    n = g.n_vertices; A = sp.lil_matrix((n, n))
    for u, v in zip(g.edge_u, g.edge_v):
        if u >= 0 and v >= 0:
            A[u, v] = A[v, u] = 1
    neg_lap = 2 * len(shape) * sp.eye(n) - A
    # in pressure variables p = c q:  p_tt = -diag(c) K K^T diag(1/c) p  should equal  -diag(c^2) neg_lap p
    lhs = sp.diags(c) @ (K @ K.T) @ sp.diags(1 / c)
    assert abs(lhs - sp.diags(c ** 2) @ neg_lap).max() < 1e-12


@pytest.mark.parametrize("form", ["paper", "graph"])
def test_both_forms_conserve_energy(form):
    from qwave.encoding import wave_hamiltonian
    g = Grid((5, 5, 5)); c, _ = head_phantom((5, 5, 5)); H = wave_hamiltonian(g, c.ravel(), form)
    assert abs(H - H.conj().T).max() < 1e-12
