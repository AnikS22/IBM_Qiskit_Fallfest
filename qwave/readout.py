"""Readout-error correction + post-selection for the unary wave circuits.

1. Calibrate: run 'all qubits 0' and 'all qubits 1' circuits; per qubit q estimate
      e0_q = P(read 1 | prepared 0),   e1_q = P(read 0 | prepared 1).
2. Correct: the observed distribution over all 2^n bitstrings is (A_{n-1} x ... x A_0) * true distribution,
   A_q = [[1-e0, e1], [e0, 1-e1]]. For n <= ~16 we invert this exactly (tensor-product inverse, cheap).
3. Post-select: the physics guarantees exactly one '1' (one excitation). Keep only weight-1 states of the
   corrected distribution and renormalise. Energy at receiver r = x[1<<r] / sum_q x[1<<q].
Error bars: bootstrap (resample shots of the data AND of the calibration circuits).
"""
import numpy as np


def counts_to_probs(counts, n):
    p = np.zeros(2 ** n)
    tot = sum(counts.values())
    for b, v in counts.items():
        p[int(b.replace(" ", ""), 2)] += v / tot
    return p


def calibrate(counts0, counts1, n):
    """Per-qubit readout error rates from the all-0 and all-1 calibration circuits."""
    p0, p1 = counts_to_probs(counts0, n), counts_to_probs(counts1, n)
    idx = np.arange(2 ** n)
    e0 = np.array([p0[(idx >> q) & 1 == 1].sum() for q in range(n)])      # read 1 although prepared 0
    e1 = np.array([p1[(idx >> q) & 1 == 0].sum() for q in range(n)])      # read 0 although prepared 1
    return e0, e1


def correct(p, e0, e1):
    """Apply the inverse tensored readout matrix to a probability vector over 2^n bitstrings."""
    n = len(e0)
    x = p.reshape((2,) * n)                    # axis k <-> qubit n-1-k (Qiskit bit order)
    for q in range(n):
        A = np.array([[1 - e0[q], e1[q]], [e0[q], 1 - e1[q]]])
        x = np.moveaxis(np.tensordot(np.linalg.inv(A), x, axes=([1], [n - 1 - q])), 0, n - 1 - q)
    return x.reshape(-1)


def receiver_energy(p, rx, n):
    w1 = np.array([1 << q for q in range(n)])
    kept = p[w1].sum()
    return p[1 << rx] / kept, kept


def estimate(counts, rx, n, cal0=None, cal1=None, n_boot=300, seed=0):
    """Raw, post-selected, and readout-corrected + post-selected receiver energy, with bootstrap errors."""
    rng = np.random.default_rng(seed)
    p = counts_to_probs(counts, n)
    shots = sum(counts.values())
    raw = p[1 << rx]
    post, kept = receiver_energy(p, rx, n)
    out = {"shots": shots, "raw": raw, "postselected": post, "kept_fraction": kept}
    if cal0 is not None:
        e0, e1 = calibrate(cal0, cal1, n)
        corr, kept_c = receiver_energy(correct(p, e0, e1), rx, n)
        out.update(corrected=corr, corrected_weight1_fraction=kept_c,
                   readout_error_mean=float(np.mean(np.concatenate([e0, e1]))))
    # bootstrap
    q0 = counts_to_probs(cal0, n) if cal0 is not None else None
    q1 = counts_to_probs(cal1, n) if cal1 is not None else None
    s0 = sum(cal0.values()) if cal0 is not None else 0
    s1 = sum(cal1.values()) if cal1 is not None else 0
    bs = {"raw": [], "postselected": [], "corrected": []}
    for _ in range(n_boot):
        pb = rng.multinomial(shots, p) / shots
        bs["raw"].append(pb[1 << rx])
        bs["postselected"].append(receiver_energy(pb, rx, n)[0])
        if cal0 is not None:
            c0 = {format(i, f"0{n}b"): v for i, v in enumerate(rng.multinomial(s0, q0)) if v}
            c1 = {format(i, f"0{n}b"): v for i, v in enumerate(rng.multinomial(s1, q1)) if v}
            e0b, e1b = calibrate(c0, c1, n)
            bs["corrected"].append(receiver_energy(correct(pb, e0b, e1b), rx, n)[0])
    # floor: a binomial error bar can't be smaller than the Laplace estimate sqrt(p(1-p)/N) with p=(k+1)/(N+2)
    n_kept = max(int(round(kept * shots)), 1)
    k_hits = p[1 << rx] * shots
    pl = (k_hits + 1) / (n_kept + 2)
    floor = float(np.sqrt(pl * (1 - pl) / n_kept))
    for k, v in bs.items():
        if v:
            out[k + "_se"] = max(float(np.std(v)), floor if k != "raw" else 0.0)
    return out
