"""Validate our solvers against Stride (Cueto, Guasch et al., Imperial College; github.com/trustimaging/stride).

Same 2D head slice, same transducers, same pulse, three Stride runs vs two of ours:

  A  Stride, constant density      p_tt = c^2 lap(p)              = the paper's physics (no attenuation)
  B  Stride, density rho = K0/c^2  p_tt = div(c^2 grad p)         = exactly the physics our QUANTUM form encodes
  C  Stride, constant density + skull attenuation                 = closer to reality (quantum form can't do this)
  a  ours (qwave/fwi.py style)      p_tt = c^2 lap(p), 2nd order  -> compare with A
  b  ours (graph Laplacian = quantum form, qwave/grid.py)          -> compare with B

Run in a Python 3.11 env with Stride installed:  python validation/compare_stride.py
"""
import sys, json, pathlib
import numpy as np
import scipy.sparse as sp

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qwave.grid import Grid as QGrid
from qwave.phantom import head_phantom, SPEEDS, LABELS

from stride import *
from stride.utils import wavelets

DX = 0.5e-3                  # 0.5 mm, the paper's grid spacing
HEAD = 100                   # 5 cm head slice (small, so it runs on a laptop)
PAD = 10                     # water around the head inside the domain
EXTRA, ABSORB = 40, 30       # Stride's absorbing padding
DT, NT = 0.04e-6, 1400       # 56 microseconds
F0, CYCLES = 0.2e6, 3        # 200 kHz tone burst (sub-MHz, as in the paper)
N_TRANS = 16
K0 = 1000.0 * 1500.0 ** 2    # bulk modulus of water


def build_medium():
    c, lab = head_phantom((HEAD, HEAD), bleed=(HEAD // 2, int(HEAD * 0.65)), bleed_radius=5, normalise=False)
    c = np.pad(c, PAD, constant_values=SPEEDS["water"]); lab = np.pad(lab, PAD, constant_values=LABELS["water"])
    return c.astype(np.float64), lab


def transducer_cells(shape, n=N_TRANS):
    ctr = (np.array(shape) - 1) / 2
    r = HEAD / 2 + 4                            # 2 mm outside the scalp
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([np.round(ctr[0] + r * np.cos(ang)), np.round(ctr[1] + r * np.sin(ang))], 1).astype(int)


# ------------------------------------------------------------------ our solvers (numpy)
def sponge(shape, width, strength=0.012):
    prof = lambda n: np.array([np.exp(-(strength * max(width - i, width - (n - 1 - i), 0)) ** 2) for i in range(n)])
    return np.outer(prof(shape[0]), prof(shape[1]))


OUR_PAD_MM = 70.0     # water padding so wide that no boundary echo returns within the recording window


def our_traces(c_inner, src, recs, wavelet, form):
    """2nd-order FD in a free-space-sized water box (no absorbing layer needed within NT*DT)."""
    pad = int(round(OUR_PAD_MM * 1e-3 / DX))
    c = np.pad(c_inner, pad, mode="edge")
    shape = c.shape
    s0 = (src[0] + pad, src[1] + pad)
    R = recs + pad
    assert pad * DX > 0.5 * NT * DT * 1500 + 2e-3, "padding too small for the recording window"
    damp = np.ones(shape)
    if form == "lap":                       # c^2 * laplacian(p)
        def L(p):
            lap = (np.roll(p, 1, 0) + np.roll(p, -1, 0) + np.roll(p, 1, 1) + np.roll(p, -1, 1) - 4 * p) / DX ** 2
            return c ** 2 * lap
    else:                                   # div(c^2 grad p): the graph Laplacian our quantum encoding uses
        g = QGrid(shape)
        B = g.incidence()
        Lmat = (B @ sp.diags(g.edge_speed(c.ravel()) ** 2) @ B.T).tocsr() / DX ** 2
        L = lambda p: -(Lmat @ p.ravel()).reshape(shape)
    p_prev = np.zeros(shape); p = np.zeros(shape); out = np.zeros((len(R), NT))
    for n in range(NT):
        p_next = 2 * p - p_prev + DT ** 2 * L(p)
        p_next[s0] += DT ** 2 * wavelet[n] * c[s0] ** 2 / DX ** 2
        p_next *= damp; p *= damp
        p_prev, p = p, p_next
        out[:, n] = p[R[:, 0], R[:, 1]]
    return out


# ------------------------------------------------------------------ Stride
async def stride_traces(runtime, c_inner, trans, wavelet, case):
    shape = c_inner.shape
    space = Space(shape=shape, extra=(EXTRA, EXTRA), absorbing=(ABSORB, ABSORB), spacing=(DX, DX))
    time = Time(start=0., step=DT, num=NT)
    problem = Problem(name=f"cmp_{case}", space=space, time=time)
    vp = ScalarField(name="vp", grid=problem.grid); vp.extended_data[:] = np.pad(c_inner, EXTRA, mode="edge")
    problem.medium.add(vp)
    kw = {"kernel": "OT2"}
    if case == "B":
        rho = ScalarField(name="rho", grid=problem.grid); rho.extended_data[:] = np.pad(K0 / c_inner ** 2, EXTRA, mode="edge")
        problem.medium.add(rho); kw["rho"] = rho
    if case == "C":
        alpha = ScalarField(name="alpha", grid=problem.grid)
        a = np.zeros(shape); _, lab = build_medium(); a[lab == LABELS["skull"]] = 8.0 * F0 / 1e6   # ~8 dB/cm/MHz at 0.2 MHz -> dB/cm (approx.)
        alpha.extended_data[:] = np.pad(a, EXTRA, mode="edge"); problem.medium.add(alpha); kw.update(alpha=alpha, attenuation_power=0)
    problem.transducers.default()
    for i, (y, x) in enumerate(trans):
        problem.geometry.add(i, problem.transducers.get(0), np.array([y * DX, x * DX]))
    loc = problem.geometry.locations
    shot = Shot(loc[0].id, sources=[loc[0]], receivers=loc, geometry=problem.geometry, problem=problem)
    problem.acquisitions.add(shot)
    shot.wavelets.data[0, :] = wavelet
    pde = IsoAcousticDevito.remote(space=space, time=time)
    sub = problem.sub_problem(shot.id)
    traces = await pde(sub.shot.wavelets, vp, problem=sub, **kw).result()
    return np.array(traces.data)


def compare(x, y, skip_source=True):
    """Normalise each set by its global max, then: relative RMS error and mean trace correlation."""
    idx = slice(1, None) if skip_source else slice(None)     # the source's own trace is grid-dependent: skip it
    x, y = x[idx], y[idx]
    x = x / np.abs(x).max(); y = y / np.abs(y).max()
    rel = float(np.linalg.norm(x - y) / np.linalg.norm(y))
    cor = float(np.mean([np.corrcoef(a, b)[0, 1] for a, b in zip(x, y)]))
    return {"relative_rms_error": rel, "mean_correlation": cor}


def our_refined(c, trans, form, fac):
    """Run our 2nd-order solver on a fac-times finer grid (same physical head), sampled back to Stride's dt."""
    global DX, DT, NT
    DX0, DT0, NT0 = DX, DT, NT
    DX, DT, NT = DX0 / fac, DT0 / fac, NT0 * fac
    try:
        wav = wavelets.tone_burst(F0, CYCLES, NT, DT).astype(np.float64)
        return our_traces(np.kron(c, np.ones((fac, fac))), trans[0] * fac, trans * fac, wav, form)[:, ::fac]
    finally:
        DX, DT, NT = DX0, DT0, NT0


async def main(runtime):
    c, lab = build_medium()
    trans = transducer_cells(c.shape)
    wav = wavelets.tone_burst(F0, CYCLES, NT, DT).astype(np.float64)
    out = {}
    S = {k: await stride_traces(runtime, c, trans, wav, k) for k in ("A", "B", "C")}
    for fac in (1, 2, 3):
        out[f"ours_lap_x{fac}_vs_stride_A"] = compare(our_refined(c, trans, "lap", fac), S["A"])
        print(fac, out[f"ours_lap_x{fac}_vs_stride_A"], flush=True)
    a = our_refined(c, trans, "lap", 3)
    b = our_refined(c, trans, "graph", 3)
    out["ours_graph_x3_vs_stride_B"] = compare(b, S["B"])
    out["stride_B_vs_A (quantum-form physics vs paper physics)"] = compare(S["B"], S["A"])
    out["stride_C_vs_A (effect of skull attenuation, missing from quantum form)"] = compare(S["C"], S["A"])
    np.savez(ROOT / "results" / "stride_comparison.npz", A=S["A"], B=S["B"], C=S["C"], a=a, b=b,
             trans=trans, c=c, dt=DT)
    json.dump(out, open(ROOT / "results" / "stride_comparison.json", "w"), indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    mosaic.run(main)
