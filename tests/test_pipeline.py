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
