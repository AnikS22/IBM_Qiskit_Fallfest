"""Fast classical replay of the *unary Trotter circuit* inside its single-excitation subspace.

The unary circuit never leaves the subspace spanned by |00..1..00>, so its exact action is a product
of small matrix exponentials of the bond layers. This reproduces the circuit's output exactly (checked
in tests/test_subspace.py) and lets us study Trotter error on grids far too big for any quantum simulator.
It is also the honest point that the unary encoding is classically easy.
"""
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import expm_multiply

from .encoding import unary_bonds, unary_qubits


def layer_matrices(grid, c):
    n = unary_qubits(grid)
    layers, used = [], []
    for a, b, h in unary_bonds(grid, c):
        for k in range(len(layers)):
            if a not in used[k] and b not in used[k]:
                layers[k].append((a, b, h)); used[k] |= {a, b}; break
        else:
            layers.append([(a, b, h)]); used.append({a, b})
    mats = []
    for L in layers:
        r, cc, v = [], [], []
        for a, b, h in L:
            r += [b, a]; cc += [a, b]; v += [h, np.conj(h)]
        mats.append(sp.csr_matrix((v, (r, cc)), shape=(n, n)))
    return mats


def trotter_receiver_energy(grid, c, t, steps, source, receivers, mats=None):
    mats = layer_matrices(grid, c) if mats is None else mats
    n = mats[0].shape[0]
    psi = np.zeros(n, dtype=complex); psi[source] = 1.0
    dt = t / steps
    seq = [(M, dt / 2) for M in mats[:-1]] + [(mats[-1], dt)] + [(M, dt / 2) for M in reversed(mats[:-1])]
    for _ in range(steps):
        for M, tau in seq:
            psi = expm_multiply(-1j * tau * M, psi)
    return np.abs(psi[np.asarray(receivers)]) ** 2
