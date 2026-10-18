"""Resource estimates: what the paper's 3D head would need, per encoding, plus the read-out wall."""
import numpy as np


def grid_counts(n_per_side, ndim=3):
    """Cells and links (including ghost boundary links) of an n^ndim grid."""
    V = n_per_side ** ndim
    E = ndim * n_per_side ** (ndim - 1) * (n_per_side + 1)       # incl. ghost boundary edges
    return V, E


def paper_head(voxel_mm=0.5, head_cm=22.0):
    """Size of the paper's head at the given voxel size: cells, links, and qubits for each encoding."""
    n = int(round(head_cm * 10 / voxel_mm))
    V, E = grid_counts(n, 3)
    return {"cells_per_side": n, "vertices": V, "edges": E,
            "compact_qubits": int(np.ceil(np.log2(V + E))), "unary_qubits": V + E}


def readout_shots(sources=1024, receivers=1024, time_samples=1000, rel_precision=0.01, p_typical=1e-3):
    """Shots to estimate every receiver trace to `rel_precision` relative error by sampling.
    Each shot lands on ONE site; a value p needs ~ (1-p)/(p*eps^2) shots for relative error eps.
    Every time sample is a separate circuit (measurement destroys the state)."""
    per_value = (1 - p_typical) / (p_typical * rel_precision ** 2)
    # one circuit per (source, time); its shots are shared across all receivers simultaneously
    return {"shots_per_circuit": per_value, "circuits": sources * time_samples,
            "total_shots": per_value * sources * time_samples,
            "numbers_needed": sources * receivers * time_samples}


def steps_needed(grid, c, t, source, receivers, rel_tol=0.05, max_steps=4096):
    """Smallest power-of-two Trotter step count whose receiver signal is within rel_tol of exact."""
    from .classical import exact_receiver_energy
    from .subspace import trotter_receiver_energy, layer_matrices
    ex = exact_receiver_energy(grid, c, [t], source, receivers)[0]
    mats = layer_matrices(grid, c)
    s = 1
    while s <= max_steps:
        p = trotter_receiver_energy(grid, c, t, s, source, receivers, mats)
        if np.abs(p - ex).max() <= rel_tol * max(ex.max(), 1e-12):
            return s
        s *= 2
    return None


def ibm_qpu_seconds(shots, jobs=1, per_shot_s=0.00035, per_job_s=2.0):
    """IBM rule of thumb (Open Plan docs): ~2 s per job + ~0.35 ms per shot (circuit-dependent)."""
    return jobs * per_job_s + shots * per_shot_s
