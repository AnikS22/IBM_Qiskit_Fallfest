"""Quantum encodings of the acoustic wave equation (Costa, Jordan & Ostrander, PRA 99, 012323, 2019).

    q_tt = -K K^T q          (K = coupling matrix, see coupling())
    phi  = [q_t ; K^T q]     (vertex block ; edge block),   |phi|^2 = total wave energy
    d phi/dt = -i H phi,   H = [[0, i K], [-i K^T, 0]]   (Hermitian)

Two ways to put phi on qubits:
  * compact (binary): basis state |k> <-> site k.  qubits = ceil(log2(n_vertices + n_edges)).
  * unary (one-hot):  one qubit per site, the wave is a single excitation hopping on the
    vertex-edge graph. qubits = n_vertices + n_edges; all gates are 2-qubit and local.
"""
import numpy as np
import scipy.sparse as sp
from qiskit.quantum_info import SparsePauliOp


def coupling(grid, c, form="paper"):
    """K (n_vertices x n_edges): how strongly each cell exchanges energy with each of its links.

    form="paper": K = diag(c_cell) B  ->  q_tt = -K K^T q with q = p/c, i.e. p_tt = c^2 * laplacian(p):
                  exactly the constant-density acoustic equation used by Guasch et al. 2020 and Stride.
    form="graph": K = B diag(c_link)  ->  p_tt = div(c^2 grad p): the original Costa et al. graph form,
                  equivalent to a medium whose density varies like 1/c^2 (kept for comparison).
    """
    B = grid.incidence()
    c = np.asarray(c).ravel()
    if form == "paper":
        return (sp.diags(c) @ B).tocsr()
    if form == "graph":
        return (B @ sp.diags(grid.edge_speed(c))).tocsr()
    raise ValueError(form)


def wave_hamiltonian(grid, c, form="paper"):
    """H = [[0, iK], [-iK^T, 0]]: Hermitian, so exp(-iHt) is a valid quantum evolution and conserves energy."""
    K = coupling(grid, c, form)
    return sp.bmat([[None, 1j * K], [-1j * K.T, None]], format="csr")


# ---------------- compact (binary) encoding ----------------
def compact_qubits(grid):
    return int(np.ceil(np.log2(grid.n_vertices + grid.n_edges)))


def compact_pauli_op(grid, c, atol=1e-12, form="paper"):
    """Pauli decomposition of the padded H. Exponential classical cost: only for small grids (<= ~9 qubits)."""
    H = wave_hamiltonian(grid, c, form)
    n = compact_qubits(grid)
    assert n <= 10, "compact Pauli decomposition is only practical for tiny grids"
    D = np.zeros((2 ** n, 2 ** n), dtype=complex)
    D[: H.shape[0], : H.shape[1]] = H.toarray()
    return SparsePauliOp.from_operator(D, atol=atol).simplify(atol=atol)


# ---------------- unary (one-hot) encoding ----------------
def unary_qubits(grid):
    return grid.n_vertices + grid.n_edges


def _bond_terms(nq, a, b, h):
    """Pauli terms for h |b><a| + h* |a><b| restricted to the single-excitation subspace."""
    def lbl(pb, pa):
        s = ["I"] * nq
        s[nq - 1 - b] = pb; s[nq - 1 - a] = pa
        return "".join(s)
    t = []
    if abs(h.real) > 0:
        t += [(lbl("X", "X"), h.real / 2), (lbl("Y", "Y"), h.real / 2)]
    if abs(h.imag) > 0:
        t += [(lbl("Y", "X"), h.imag / 2), (lbl("X", "Y"), -h.imag / 2)]
    return t


def unary_bonds(grid, c, form="paper"):
    """List of (a, b, h) with h = H[b, a], a = vertex site, b = edge site."""
    H = wave_hamiltonian(grid, c, form).tocoo()
    return [(int(j), int(i), complex(v)) for i, j, v in zip(H.row, H.col, H.data) if i > j]


def unary_layers(grid, c):
    """Greedy colouring of bonds into layers of disjoint qubit pairs; returns list of SparsePauliOp.
    Each layer is a sum of commuting terms, so exp(-i layer dt) is exact; Trotter error is between layers."""
    nq = unary_qubits(grid)
    layers, used = [], []
    for a, b, h in unary_bonds(grid, c):
        for k in range(len(layers)):
            if a not in used[k] and b not in used[k]:
                layers[k].append((a, b, h)); used[k] |= {a, b}; break
        else:
            layers.append([(a, b, h)]); used.append({a, b})
    ops = []
    for L in layers:
        terms = []
        for a, b, h in L:
            terms += _bond_terms(nq, a, b, h)
        ops.append(SparsePauliOp.from_list(terms))
    return ops


def unary_full_op(grid, c):
    ops = unary_layers(grid, c)
    tot = ops[0]
    for o in ops[1:]:
        tot = tot + o
    return tot.simplify()
