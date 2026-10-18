"""Classical reference solvers for q_tt = -K K^T q (any dimension); K from qwave.encoding.coupling.

With form="paper" (default) q = p/c and this is p_tt = c^2 laplacian(p), the paper's / Stride's equation.
Energy read-outs are fractions of the total wave energy, matching what the quantum measurement returns."""
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import expm_multiply

from .encoding import wave_hamiltonian, coupling


def laplacian(grid, c, form="paper"):
    """Discrete wave operator L = K K^T (sparse CSR), so the classical model is q_tt = -L q."""
    K = coupling(grid, c, form)
    return (K @ K.T).tocsr()


def fd_receiver_energy(grid, c, times, source, receivers, dt=2e-3):
    """Velocity-Verlet finite differences. Initial condition: unit velocity kick at `source` cell.
    Returns (len(times), len(receivers)) kinetic-energy fraction v[r]^2 / E_total at each receiver."""
    L = laplacian(grid, c)
    n = grid.n_vertices
    u = np.zeros(n); v = np.zeros(n); v[source] = 1.0
    a = -(L @ u)
    out, t, k, times = [], 0.0, 0, list(times)
    while k < len(times):
        if t >= times[k] - 1e-12:
            out.append(v[receivers] ** 2); k += 1; continue
        v_half = v + 0.5 * dt * a
        u = u + dt * v_half
        a = -(L @ u)
        v = v_half + 0.5 * dt * a
        t += dt
    return np.array(out)


def exact_receiver_energy(grid, c, times, source, receivers):
    """Exact solution via the first-order (Schrodinger-form) system: |psi(t)[r]|^2 = kinetic-energy fraction."""
    H = wave_hamiltonian(grid, c).tocsc()
    psi0 = np.zeros(H.shape[0], dtype=complex); psi0[source] = 1.0
    out = []
    for t in times:
        psi = psi0 if t == 0 else expm_multiply(-1j * t * H, psi0)
        out.append(np.abs(psi[receivers]) ** 2)
    return np.array(out)


def total_energy_fd(grid, c, T, source, dt=2e-3):
    """Energy at time T (should stay 1.0)."""
    L = laplacian(grid, c); n = grid.n_vertices
    u = np.zeros(n); v = np.zeros(n); v[source] = 1.0; a = -(L @ u)
    for _ in range(int(round(T / dt))):
        v_half = v + 0.5 * dt * a; u = u + dt * v_half; a = -(L @ u); v = v_half + 0.5 * dt * a
    return float(v @ v + u @ (L @ u))
