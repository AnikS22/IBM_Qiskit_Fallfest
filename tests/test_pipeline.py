"""Hardware helpers, hybrid demo and classical FWI behave as claimed."""
import numpy as np
from qwave.hardware import ray_problem, fold, analyse_counts, build_circuits
from qwave.resources import paper_head


def test_ray_goes_through_skull_and_bleed():
    _, c, lab = ray_problem(bleed=True)
    assert list(lab) == [1, 2, 3, 4, 3, 2, 1]


def test_fold_triples_depth():
    circs, _ = build_circuits(steps_list=(2,), folds=(1, 3))
    assert circs[1].size() > 2.5 * circs[0].remove_final_measurements(inplace=False).size()


def test_postselection_logic():
    r = analyse_counts({"001": 50, "010": 30, "011": 20}, receiver_qubit=0, n_qubits=3)
    assert r["raw"] == 0.5 and abs(r["postselected"] - 50 / 80) < 1e-12 and r["kept_fraction"] == 0.8


def test_paper_head_scale():
    h = paper_head()
    assert h["cells_per_side"] == 440 and h["compact_qubits"] == 29


def test_hybrid_exact_misfit_finds_bleed():
    from qwave.hybrid import setup, run_trials
    P = setup()
    r = run_trials(P, shots_list=(10**11,), trials=3)
    assert r["exact_pick_correct"] and r["success"][10**11] == 1.0


def test_fwi_gradient_points_toward_bleed():
    import jax.numpy as jnp
    from qwave.fwi import make_problem, simulate_all, invert
    P = make_problem(n_head=40, pad=12, n_trans=12, bleed=(12, 22), bleed_radius=3)
    d = simulate_all(P, P["c_true"])
    c_est, hist = invert(P, d, iters=15, batch=6, lr=3.0, verbose=False)
    bleed = P["lab"] == 4
    assert c_est[bleed].mean() > P["c0"][bleed].mean() + 5     # moved toward the faster blood


def test_readout_correction_recovers_true_distribution():
    """Apply known per-qubit readout errors to a known distribution; the correction must undo them exactly."""
    from qwave.readout import correct
    n = 4
    rng = np.random.default_rng(0)
    true = np.zeros(2 ** n); true[[1, 2, 4, 8]] = [0.1, 0.2, 0.3, 0.4]          # single-excitation states
    e0, e1 = rng.uniform(0.01, 0.05, n), rng.uniform(0.02, 0.08, n)
    x = true.reshape((2,) * n)
    for q in range(n):
        A = np.array([[1 - e0[q], e1[q]], [e0[q], 1 - e1[q]]])
        x = np.moveaxis(np.tensordot(A, x, axes=([1], [n - 1 - q])), 0, n - 1 - q)
    noisy = x.reshape(-1)
    assert np.abs(correct(noisy, e0, e1) - true).max() < 1e-12


def test_light_cone_truncation_is_valid():
    """The 9-qubit hardware circuit (first 4 cells) gives the same receiver energy as the full 15-qubit line."""
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location("v2", pathlib.Path(__file__).parents[1] / "hardware" / "run_ibm_v2.py")
    v2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v2)
    v2.problem()          # asserts |full - truncated| < 2e-3 at every measured time
