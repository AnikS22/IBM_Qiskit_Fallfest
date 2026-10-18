"""Hybrid inversion demo on a tiny 3D head: quantum supplies ONE number (misfit), classical does the search.

For each candidate bleed location the 'quantum forward model' is ideal compact-encoding evolution
exp(-iHt)|source> on ceil(log2(V+E)) qubits, read out by SAMPLING (finite shots): one shot = one site index,
so every receiver's energy fraction is estimated from the same shots. The classical outer loop picks the
candidate with the smallest misfit. Shot noise is the honest cost being measured.
"""
import numpy as np
from scipy.sparse.linalg import expm_multiply

from .grid import Grid
from .phantom import head_phantom, transducers, LABELS
from .encoding import wave_hamiltonian, compact_qubits


def setup(shape=(7, 7, 7), true_bleed=None, times=(2.0, 3.0, 4.0)):
    """Tiny 3D hybrid test: source = first surface cell, receivers = other surface cells,
    candidates = no bleed or a bleed in any brain cell. Returns a dict."""
    g = Grid(shape)
    c_h, lab = head_phantom(shape)
    brain = [tuple(x) for x in np.argwhere(lab == LABELS["brain"])]
    true_bleed = true_bleed or brain[len(brain) // 2 + 1]
    surf = transducers(lab)
    src = g.index(*surf[0])                                  # first transducer fires
    rx = [g.index(*s) for s in surf[1:]]                     # every other surface cell listens
    cands = [None] + brain
    return dict(grid=g, lab=lab, brain=brain, true=true_bleed, src=src, rx=np.array(rx), times=times, cands=cands,
                qubits=compact_qubits(g))


def site_probs(P, bleed):
    """Exact |psi(t)|^2 over ALL sites (vertices+edges) for each time: the ideal quantum measurement distribution."""
    c, _ = head_phantom(P["grid"].shape, bleed=bleed)
    H = wave_hamiltonian(P["grid"], c.ravel()).tocsc()
    psi0 = np.zeros(H.shape[0], complex); psi0[P["src"]] = 1
    return [np.abs(expm_multiply(-1j * t * H, psi0)) ** 2 for t in P["times"]]


def misfit(pred, meas, rx):
    """Sum of squared differences between predicted and measured energies at the receivers, over all times."""
    return float(sum(np.sum((p[rx] - m[rx]) ** 2) for p, m in zip(pred, meas)))


def run_trials(P, shots_list=(10**3, 10**4, 10**5, 10**6), trials=20, seed=0):
    """Measured data = exact receiver energies of the true head (stand-in for the helmet's measurement).
    Quantum estimate for each candidate = multinomial sampling of its site distribution with S shots."""
    rng = np.random.default_rng(seed)
    meas = site_probs(P, P["true"])
    exact = {k: site_probs(P, b) for k, b in enumerate(P["cands"])}
    exact_mis = np.array([misfit(exact[k], meas, P["rx"]) for k in exact])
    truth = P["cands"].index(P["true"])
    out = {"exact_pick_correct": int(np.argmin(exact_mis)) == truth, "exact_misfits": exact_mis, "success": {}}
    for S in shots_list:
        ok = 0
        for _ in range(trials):
            mis = []
            for k in exact:
                est = [rng.multinomial(S, p / p.sum()) / S for p in exact[k]]
                mis.append(misfit(est, meas, P["rx"]))
            ok += int(np.argmin(mis) == truth)
        out["success"][S] = ok / trials
    return out


def run_detection(P, shots_list, trials=20, seed=1):
    """Easier yes/no question: is the measured head closer to 'bleed at true spot' or 'no bleed'?"""
    rng = np.random.default_rng(seed)
    meas = site_probs(P, P["true"])
    models = {"none": site_probs(P, None), "bleed": site_probs(P, P["true"])}
    out = {}
    for S in shots_list:
        ok = 0
        for _ in range(trials):
            mis = {k: misfit([rng.multinomial(S, p / p.sum()) / S for p in v], meas, P["rx"]) for k, v in models.items()}
            ok += int(mis["bleed"] < mis["none"])
        out[S] = ok / trials
    return out
