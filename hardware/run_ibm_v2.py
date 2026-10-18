"""Hardware experiment v2: watch the sound wave arrive through the skull on a real quantum computer.

Improvements over v1 (lessons from the ibm_marrakesh run, job db9smd9gv2cc73e60pm0):
  * Light-cone truncation: only the first 4 cells (scalp, skull, brain, brain) can influence the receiver
    within t <= 3, so the circuit needs 9 qubits instead of 15 (difference vs full line < 0.001, checked below).
  * Readout-error correction (qwave/readout.py) from two calibration circuits, then post-selection.
  * Gate AND measurement twirling + dynamical decoupling on hardware.
  * A time trace: energy at the receiver at t = 0.5 ... 3.0 (the wave arriving, peaking, leaving),
    plus a x3 noise-folded copy at t = 1.0 and 1.5 for zero-noise extrapolation.

PRE-REGISTERED SUCCESS CRITERION (written before the run):
  The readout-corrected + post-selected hardware trace is within 2 standard errors of the ideal circuit
  value at >= 5 of the 6 times, AND its correlation with the exact classical trace is >= 0.9.

Usage
  python hardware/run_ibm_v2.py --dry-run           # free rehearsal on FakeMarrakesh (IBM's noise model of that chip)
  IBM_QUANTUM_TOKEN=... python hardware/run_ibm_v2.py [--backend ibm_marrakesh]
"""
import argparse, json, os, sys, time, pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qwave.grid import Grid
from qwave.hardware import ray_problem, fold
from qwave.circuits import unary_circuit
from qwave.classical import exact_receiver_energy
from qwave.subspace import trotter_receiver_energy
from qwave.readout import estimate

TIMES = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)
DT = 0.25
CELLS = 4                          # scalp, skull, brain, brain
RX, SRC = 2, 0                     # receiver = first brain cell (qubit 2), source = scalp (qubit 0)
FOLD_TIMES = (1.0, 1.5)
SHOTS = int(os.environ.get("SHOTS", 4000))


def problem():
    """Light-cone 4-cell problem. Checks it matches the full 7-cell line, then returns (grid, speeds, steps, exact, ideal)."""
    g7, c7, lab7 = ray_problem()
    g, c = Grid((CELLS,)), c7[:CELLS]
    exact_full = exact_receiver_energy(g7, c7, TIMES, SRC, [RX]).ravel()
    exact_trunc = exact_receiver_energy(g, c, TIMES, SRC, [RX]).ravel()
    assert np.abs(exact_full - exact_trunc).max() < 2e-3, "light-cone truncation not valid"
    steps = [int(np.ceil(t / DT)) for t in TIMES]
    ideal = [float(trotter_receiver_energy(g, c, t, s, SRC, [RX])[0]) for t, s in zip(TIMES, steps)]
    return g, c, steps, exact_full, ideal


def build(g, c, steps):
    """Calibration circuits plus one measured circuit per time (and a x3 fold at FOLD_TIMES); returns (n_qubits, circuits, meta)."""
    n = g.n_vertices + g.n_edges
    circs, meta = [], []
    cal0 = QuantumCircuit(n); cal0.measure_all()
    cal1 = QuantumCircuit(n); cal1.x(range(n)); cal1.measure_all()
    circs += [cal0, cal1]; meta += [{"kind": "cal0"}, {"kind": "cal1"}]
    for t, s in zip(TIMES, steps):
        qc = unary_circuit(g, c, t, s, SRC); qc.measure_all()
        circs.append(qc); meta.append({"kind": "trace", "t": t, "steps": s, "fold": 1})
        if t in FOLD_TIMES:
            circs.append(fold(qc, 3)); meta.append({"kind": "trace", "t": t, "steps": s, "fold": 3})
    return n, circs, meta


def get_backend(dry_run, name):
    """FakeMarrakesh for --dry-run; otherwise an IBM backend (token from IBM_QUANTUM_TOKEN or a hidden prompt, never saved)."""
    if dry_run:
        from qiskit_ibm_runtime.fake_provider import FakeMarrakesh
        return FakeMarrakesh()
    from qiskit_ibm_runtime import QiskitRuntimeService
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        import getpass
        token = getpass.getpass("IBM Quantum API key (not stored): ")
    kw = {"token": token}
    if os.environ.get("IBM_QUANTUM_INSTANCE"):
        kw["instance"] = os.environ["IBM_QUANTUM_INSTANCE"]
    service = QiskitRuntimeService(**kw)
    return service.backend(name) if name else service.least_busy(simulator=False, operational=True, min_num_qubits=9)


def run(circs, backend, dry_run):
    """Transpile (opt. level 3) and run all circuits in one Sampler job; returns (job, isa circuits, counts)."""
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend, seed_transpiler=7)
    isa = pm.run(circs)
    try:
        from qiskit_ibm_runtime.executor_sampler import Sampler
    except ImportError:                                   # older qiskit-ibm-runtime
        from qiskit_ibm_runtime import SamplerV2 as Sampler
    sampler = Sampler(mode=backend)
    sampler.options.default_shots = SHOTS
    if not dry_run:
        sampler.options.dynamical_decoupling.enable = True
        sampler.options.twirling.enable_gates = True
        sampler.options.twirling.enable_measure = True
    job = sampler.run(isa)
    print("job id:", job.job_id())
    res = job.result()
    counts = []
    for r in res:
        try:
            counts.append(r.join_data().get_counts())
        except AttributeError:
            counts.append(r.data.meas.get_counts())
    return job, isa, counts


def analyse(n, meta, isa, counts, exact, ideal):
    """Readout-corrected + post-selected energies, ZNE from folds 1 and 3, and the pre-registered verdict."""
    cal0 = counts[[m["kind"] for m in meta].index("cal0")]
    cal1 = counts[[m["kind"] for m in meta].index("cal1")]
    rows = []
    for m, ic, cn in zip(meta, isa, counts):
        if m["kind"] != "trace":
            continue
        k = TIMES.index(m["t"])
        est = estimate(cn, RX, n, cal0, cal1)
        rows.append({**m, "cz": int(ic.count_ops().get("cz", 0)), "exact": float(exact[k]), "ideal_circuit": ideal[k], **est})
    trace = [r for r in rows if r["fold"] == 1]
    hits = sum(abs(r["corrected"] - r["ideal_circuit"]) <= 2 * r["corrected_se"] for r in trace)
    corr = float(np.corrcoef([r["corrected"] for r in trace], [r["exact"] for r in trace])[0, 1])
    zne = {}
    for t in FOLD_TIMES:
        r1 = next(r for r in rows if r["t"] == t and r["fold"] == 1); r3 = next(r for r in rows if r["t"] == t and r["fold"] == 3)
        for key in ("postselected", "corrected"):
            zne[f"t={t} {key}"] = {"value": r1[key] + (r1[key] - r3[key]) / 2,
                                   "se": float(np.hypot(1.5 * r1[key + "_se"], 0.5 * r3[key + "_se"]))}
    verdict = {"points_within_2se_of_ideal": f"{hits}/{len(trace)}", "correlation_with_exact": corr,
               "criterion_met": bool(hits >= 5 and corr >= 0.9)}
    return rows, zne, verdict


def main():
    """Run on hardware or a fake backend, or recompute the analysis of a saved JSON with --reanalyse (no QPU)."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--reanalyse", default=None, help="path to a saved results JSON: recompute analysis, no QPU")
    a = ap.parse_args()
    g, c, steps, exact, ideal = problem()
    if a.reanalyse:
        d = json.load(open(a.reanalyse))
        meta = [{k: v for k, v in rc.items() if k != "counts"} for rc in d["raw_counts"]]
        counts = [rc["counts"] for rc in d["raw_counts"]]
        cz = {(r["t"], r["fold"]): r["cz"] for r in d["rows"]}
        class _C:                                   # stand-in for transpiled circuits (only gate counts are needed)
            def __init__(self, n): self.n = n
            def count_ops(self): return {"cz": self.n}   # analyse() only reads the CZ count
        isa = [_C(cz.get((m.get("t"), m.get("fold")), 0)) for m in meta]
        rows, zne, verdict = analyse(d["qubits"], meta, isa, counts, exact, ideal)
        d.update(rows=rows, zne=zne, verdict=verdict)
        json.dump(d, open(a.reanalyse, "w"), indent=1, default=float)
        for r in rows:
            print(r["t"], r["fold"], f"ideal {r['ideal_circuit']:.4f} corrected {r['corrected']:.4f} ± {r['corrected_se']:.4f}")
        print("VERDICT:", verdict); return
    n, circs, meta = build(g, c, steps)
    backend = get_backend(a.dry_run, a.backend)
    print(f"backend {backend.name}: {len(circs)} circuits x {SHOTS} shots on {n} qubits")
    t0 = time.time()
    job, isa, counts = run(circs, backend, a.dry_run)
    rows, zne, verdict = analyse(n, meta, isa, counts, exact, ideal)
    out = {"backend": backend.name, "dry_run": a.dry_run, "job_id": job.job_id(), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "shots": SHOTS, "qubits": n, "criterion": "corrected within 2 SE of ideal at >=5/6 times AND corr(exact) >= 0.9",
           "verdict": verdict, "zne": zne, "rows": rows, "raw_counts": [{**m, "counts": cn} for m, cn in zip(meta, counts)]}
    path = ROOT / "results" / f"hardware_v2_{backend.name}{'_DRYRUN' if a.dry_run else ''}.json"
    json.dump(out, open(path, "w"), indent=1, default=float)
    print(f"{'t':>4} {'exact':>7} {'ideal':>7} {'raw':>7} {'post':>13} {'corrected':>15} {'kept':>6}")
    for r in rows:
        tag = "" if r["fold"] == 1 else " (x3 fold)"
        print(f"{r['t']:4.1f} {r['exact']:7.3f} {r['ideal_circuit']:7.3f} {r['raw']:7.3f} "
              f"{r['postselected']:6.3f}±{r['postselected_se']:.3f} {r['corrected']:7.3f}±{r['corrected_se']:.3f} {r['kept_fraction']:6.1%}{tag}")
    print("ZNE:", json.dumps(zne, indent=1)); print("VERDICT:", verdict); print("saved", path, f"({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
