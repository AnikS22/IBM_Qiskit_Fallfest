"""Classical full-waveform inversion baseline (2D, JAX autodiff = adjoint-state gradient).

Mirrors the paper's haemorrhage test (Guasch et al. 2020, Fig. 8): true skull known, brain starts
homogeneous, invert transcranial data for brain sound speed and look for the bleed. Runs on a laptop in 2D;
the same code runs in 3D on a GPU node (set shape to 3D and install jax[cuda12]).
"""
import numpy as np
import jax
import jax.numpy as jnp
from functools import partial

from .phantom import head_phantom, LABELS, SPEEDS

jax.config.update("jax_enable_x64", False)


def head_in_water(n_head=72, pad=16, bleed=None, bleed_radius=0):
    c, lab = head_phantom((n_head, n_head), bleed=bleed, bleed_radius=bleed_radius, normalise=False)
    c = np.pad(c, pad, constant_values=SPEEDS["water"]); lab = np.pad(lab, pad, constant_values=LABELS["water"])
    return c, lab


def ring_transducers(shape, n_trans=32, radius=None):
    cy, cx = (shape[0] - 1) / 2, (shape[1] - 1) / 2
    radius = radius or 0.5 * min(shape) - 10
    ang = np.linspace(0, 2 * np.pi, n_trans, endpoint=False)
    return np.stack([np.round(cy + radius * np.sin(ang)), np.round(cx + radius * np.cos(ang))], 1).astype(int)


def ricker(nt, dt, f0):
    t = np.arange(nt) * dt - 1.2 / f0
    a = (np.pi * f0 * t) ** 2
    return ((1 - 2 * a) * np.exp(-a)).astype(np.float32)


def sponge(shape, width=12, strength=0.015):
    d = np.ones(shape, np.float32)
    for ax in range(2):
        n = shape[ax]
        prof = np.ones(n, np.float32)
        r = np.arange(width)
        prof[:width] = np.exp(-(strength * (width - r)) ** 2)
        prof[-width:] = prof[:width][::-1]
        d *= prof[:, None] if ax == 0 else prof[None, :]
    return d


@partial(jax.jit, static_argnames=("nt",))
def forward(c, src_pos, rec_pos, wavelet, damp, dx, dt, nt):
    """Pressure at receivers for ONE source. c: (ny,nx) m/s."""
    k = (c * dt / dx) ** 2

    def step(carry, w):
        p_prev, p = carry
        lap = (jnp.roll(p, 1, 0) + jnp.roll(p, -1, 0) + jnp.roll(p, 1, 1) + jnp.roll(p, -1, 1) - 4 * p)
        p_next = (2 * p - p_prev + k * lap).at[src_pos[0], src_pos[1]].add(w)
        p_next = p_next * damp; p = p * damp
        return (p, p_next), p_next[rec_pos[:, 0], rec_pos[:, 1]]

    z = jnp.zeros_like(c)
    _, rec = jax.lax.scan(step, (z, z), wavelet)
    return rec                                         # (nt, n_rec)


def make_problem(n_head=72, pad=16, dx=2.5e-3, f0=60e3, n_trans=32, bleed=(20, 44), bleed_radius=4):
    c_true, lab = head_in_water(n_head, pad, bleed=bleed, bleed_radius=bleed_radius)
    c_heal, _ = head_in_water(n_head, pad)
    shape = c_true.shape
    dt = 0.4 * dx / c_true.max()
    nt = int(1.6 * (shape[0] * dx / 1500.0) / dt)
    trans = ring_transducers(shape, n_trans)
    brain = np.isin(lab, [LABELS["brain"], LABELS["blood"]])
    c0 = np.where(brain, SPEEDS["brain"], c_true).astype(np.float32)   # skull known, brain homogeneous
    return dict(c_true=c_true.astype(np.float32), c_healthy=c_heal.astype(np.float32), c0=c0, brain=brain, lab=lab,
                trans=trans, dx=dx, dt=dt, nt=nt, wavelet=ricker(nt, dt, f0), damp=sponge(shape))


def simulate_all(P, c):
    f = jax.vmap(lambda s: forward(jnp.asarray(c), s, jnp.asarray(P["trans"]), jnp.asarray(P["wavelet"]),
                                   jnp.asarray(P["damp"]), P["dx"], P["dt"], P["nt"]))
    return f(jnp.asarray(P["trans"]))                  # (n_src, nt, n_rec)


def invert(P, data, iters=40, batch=8, lr=3.0, seed=0, verbose=True):
    """Adam on brain sound speed; gradient by JAX reverse-mode (= discrete adjoint-state method)."""
    mask = jnp.asarray(P["brain"], jnp.float32)
    c_fixed = jnp.asarray(P["c0"])
    trans = jnp.asarray(P["trans"])

    def loss(dc, idx):
        c = c_fixed + mask * dc
        pred = jax.vmap(lambda s: forward(c, s, trans, jnp.asarray(P["wavelet"]), jnp.asarray(P["damp"]),
                                          P["dx"], P["dt"], P["nt"]))(trans[idx])
        return 0.5 * jnp.sum((pred - data[idx]) ** 2) / jnp.sum(data[idx] ** 2)

    g_fn = jax.jit(jax.value_and_grad(loss))
    dc = jnp.zeros_like(c_fixed); m = jnp.zeros_like(dc); v = jnp.zeros_like(dc)
    rng = np.random.default_rng(seed); hist = []
    scale = None
    for it in range(1, iters + 1):
        idx = jnp.asarray(rng.choice(len(P["trans"]), batch, replace=False))
        L, g = g_fn(dc, idx)
        g = g * mask
        m = 0.9 * m + 0.1 * g; v = 0.999 * v + 0.001 * g * g
        mh = m / (1 - 0.9 ** it); vh = v / (1 - 0.999 ** it)
        dc = dc - lr * mh / (jnp.sqrt(vh) + 1e-12)
        hist.append(float(L))
        if verbose and (it % 10 == 0 or it == 1):
            print(f"iter {it:3d}  misfit {float(L):.3e}")
    return np.asarray(c_fixed + mask * dc), hist
