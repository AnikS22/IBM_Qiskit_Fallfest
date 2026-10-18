"""README animations, all computed with qwave (nothing hand-drawn).

  docs/wave_head.gif         sound from one transducer crossing a 2D head slice with a bleed (classical finite differences)
  docs/quantum_vs_classical.gif  same physics: what the unary quantum circuit computes vs the exact classical answer
Run: PYTHONPATH=. venv/bin/python3 docs/make_animations.py   (~1 min, no QPU)
"""
import pathlib
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap
from scipy.sparse.linalg import expm_multiply

from qwave.grid import Grid
from qwave.phantom import head_phantom
from qwave.classical import laplacian
from qwave.encoding import wave_hamiltonian
from qwave.subspace import layer_matrices

OUT = pathlib.Path(__file__).resolve().parent
BG, FG, ACC = "#05070B", "#F7F8FA", "#7FA2E8"
WAVE = LinearSegmentedColormap.from_list("w", ["#3B5B9F", BG, "#F2C14E"])
plt.rcParams.update({"text.color": FG, "axes.labelcolor": FG, "font.size": 11})


def wave_head(n=110, frames=90):
    """2D head slice with a bleed; velocity-Verlet finite differences from a smooth source left of the head -> wave_head.gif."""
    bleed = (int(n * .62), int(n * .40))
    c, lab = head_phantom((n, n), bleed=bleed, bleed_radius=n * .06)
    g = Grid((n, n)); L = laplacian(g, c.ravel())
    dt = 0.4 * 2 / np.sqrt(abs(L.diagonal()).max() * 2)        # well inside stability: no grid-scale noise
    yy, xx = np.mgrid[:n, :n]                                  # smooth transducer pulse, not a one-cell kick
    u = np.zeros(g.n_vertices); a = -(L @ u)
    v = np.exp(-((yy - n // 2) ** 2 + (xx - 6) ** 2) / (2 * 2.5 ** 2)).ravel()
    per = int(0.95 * n / frames / dt) + 1
    fig, ax = plt.subplots(figsize=(5, 5), facecolor=BG); ax.set_axis_off()
    ax.imshow(c, cmap="Greys_r", alpha=.55)
    ax.contour(lab == lab[bleed], levels=[.5], colors="#E74C3C", linewidths=1.2)
    im = ax.imshow(np.zeros((n, n)), cmap=WAVE, vmin=-1, vmax=1, alpha=.85)
    ax.set_title("Sound crossing the skull and a bleed (red)", color=FG, fontsize=11)

    def step(_):
        """Advance `per` time steps and draw the velocity field (signed square root for contrast)."""
        nonlocal u, v, a
        for _ in range(per):
            vh = v + .5 * dt * a; u = u + dt * vh; a = -(L @ u); v = vh + .5 * dt * a
        f = v.reshape(n, n); im.set_data(np.sign(f) * np.abs(f / (abs(f).max() + 1e-12)) ** .5)
        return im,
    FuncAnimation(fig, step, frames=frames, blit=True).save(OUT / "wave_head.gif", writer=PillowWriter(fps=18),
                                                            savefig_kwargs={"facecolor": BG})
    plt.close(fig)


def quantum_vs_classical(n=31, frames=60, steps_per_frame=6):
    """Unary circuit = Strang-Trotter product of bond layers; replayed exactly in its 1-excitation subspace."""
    c, _ = head_phantom((n, n)); g = Grid((n, n)); cc = c.ravel()
    H = wave_hamiltonian(g, cc).tocsc(); mats = layer_matrices(g, cc)
    src = g.index(n // 2, n // 2)
    T = 0.55 * n; dt = T / (frames * steps_per_frame)
    seq = [(M, dt / 2) for M in mats[:-1]] + [(mats[-1], dt)] + [(M, dt / 2) for M in reversed(mats[:-1])]
    psi_q = np.zeros(H.shape[0], complex); psi_q[src] = 1
    psi_c = psi_q.copy()
    fig, axs = plt.subplots(1, 2, figsize=(8, 4.3), facecolor=BG)
    ims = []
    for ax, t in zip(axs, ("Quantum circuit (Qiskit unary encoding)", "Classical exact solver")):
        ax.set_axis_off(); ax.set_title(t, color=FG, fontsize=10)
        ims.append(ax.imshow(np.zeros((n, n)), cmap="magma", vmin=0, vmax=1))
    txt = fig.text(.5, .04, "", ha="center", color=ACC, fontsize=10)

    def step(k):
        """Advance both solvers by one frame and draw them; caption = max energy difference as % of the peak."""
        nonlocal psi_q, psi_c
        for _ in range(steps_per_frame):
            for M, tau in seq: psi_q = expm_multiply(-1j * tau * M, psi_q)
        psi_c = expm_multiply(-1j * dt * steps_per_frame * H, psi_c)
        eq, ec = (np.abs(p[:g.n_vertices]) ** 2 for p in (psi_q, psi_c))
        m = max(eq.max(), ec.max())
        for im, e in zip(ims, (eq, ec)): im.set_data((e.reshape(n, n) / m) ** .4)
        txt.set_text(f"max difference {np.abs(eq - ec).max() / ec.max():.1%} of peak")
        return (*ims, txt)
    FuncAnimation(fig, step, frames=frames, blit=False).save(OUT / "quantum_vs_classical.gif", writer=PillowWriter(fps=14),
                                                             savefig_kwargs={"facecolor": BG})
    plt.close(fig)


if __name__ == "__main__":
    wave_head(); print("wave_head.gif")
    quantum_vs_classical(); print("quantum_vs_classical.gif")
