"""The real-hardware experiment (follows IBM's current 'hello world' guide, qiskit-ibm-runtime >= 0.50).

What it runs on ONE IBM QPU, in ONE batch:
  Job 1  Sampler  : the 15-qubit ear-to-ear wave circuit through the 3D head phantom
                    healthy @ 2,4,6,8 Trotter steps, bleed @ 8 steps, healthy @ 8 steps noise-tripled (U U^dag U)
                    -> raw energy, post-selected energy (exactly-one-excitation rule), manual ZNE
  Job 2  Estimator (optional, --with-estimator): the same physics as an expectation value E = (1 - <Z_receiver>)/2 at 4 and 8 steps,
                    with IBM's built-in error handling at resilience levels 0 (none), 1 (readout, TREX), 2 (ZNE)
Everything is compared against the exact classical answer and saved to results/hardware_<backend>_<time>.json.

Usage
  python hardware/run_ibm.py --dry-run            # free: same code path on the FakeKingston noise model
  IBM_QUANTUM_TOKEN=... python hardware/run_ibm.py # real QPU (~30-60 s of the 10 free minutes)
The API key is read from the environment and never written to disk.
"""
import argparse, json, os, sys, time, pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qwave.hardware import ray_problem, fold, analyse_counts
from qwave.encoding import unary_layers
from qwave.circuits import unary_circuit
from qwave.classical import exact_receiver_energy

T, RX, SRC = 1.5, 2, 0           # time, receiver = first brain cell past the skull (qubit 2), source = scalp (qubit 0)
SAMPLER_SHOTS = int(os.environ.get("SHOTS", 4000))
EST_SHOTS = int(os.environ.get("SHOTS", 4000))


def build():
    """v1 circuits (healthy at 2/4/6/8 steps, bleed at 8, healthy at 8 folded x3), Estimator circuits, and exact answers."""
    circs, meta = [], []
    for bleed, steps, factor in [(False, 2, 1), (False, 4, 1), (False, 6, 1), (False, 8, 1), (True, 8, 1), (False, 8, 3)]:
        g, c, _ = ray_problem(bleed=bleed)
        qc = unary_circuit(g, c, T, steps, SRC, unary_layers(g, c))
        qc.measure_all()
        circs.append(fold(qc, factor) if factor > 1 else qc)
        meta.append({"bleed": bleed, "steps": steps, "fold": factor})
    exact = {b: float(exact_receiver_energy(*ray_problem(bleed=b)[:2], [T], SRC, [RX])[0, 0]) for b in (False, True)}
    est = []
    for steps in (4, 8):
        g, c, _ = ray_problem()
        est.append((steps, unary_circuit(g, c, T, steps, SRC, unary_layers(g, c))))
    return circs, meta, est, exact


def get_backend(dry_run, name):
    """FakeKingston for --dry-run; otherwise an IBM backend (token from IBM_QUANTUM_TOKEN or a hidden prompt, never saved)."""
    if dry_run:
        from qiskit_ibm_runtime.fake_provider import FakeKingston
        return FakeKingston()
    from qiskit_ibm_runtime import QiskitRuntimeService
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        import getpass
        token = getpass.getpass("IBM Quantum API key (not stored): ")
    kw = {"token": token}
    if os.environ.get("IBM_QUANTUM_INSTANCE"):
        kw["instance"] = os.environ["IBM_QUANTUM_INSTANCE"]
    service = QiskitRuntimeService(**kw)
    return service.backend(name) if name else service.least_busy(simulator=False, operational=True, min_num_qubits=15)


def main():
    """Build, transpile, run the Sampler job (and optionally the Estimator job), analyse and save results."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="use FakeKingston locally (free)")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--with-estimator", action="store_true", help="also run IBM built-in mitigation (Estimator, levels 0-2); untested locally")
    a = ap.parse_args()

    circs, meta, est, exact = build()
    backend = get_backend(a.dry_run, a.backend)
    print("backend:", backend.name, "| exact energy (healthy, bleed):", exact)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend, seed_transpiler=7)
    isa = pm.run(circs)
    for m, c in zip(meta, isa):
        m.update(cz=int(sum(v for k, v in c.count_ops().items() if k in ("cz", "ecr", "cx"))), depth=int(c.depth()))
    print("two-qubit gates per circuit:", [m["cz"] for m in meta])

    from qiskit_ibm_runtime.executor_sampler import Sampler
    from qiskit_ibm_runtime.executor_estimator import Estimator
    from qiskit_ibm_runtime.options_models import EstimatorOptions
    out = {"backend": backend.name, "dry_run": a.dry_run, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "T": T, "receiver_qubit": RX, "exact": {"healthy": exact[False], "bleed": exact[True]}}

    # ---------------- Job 1: Sampler (raw + post-selection + manual ZNE)
    sampler = Sampler(mode=backend)
    sampler.options.default_shots = SAMPLER_SHOTS
    if not a.dry_run:
        sampler.options.dynamical_decoupling.enable = True
        sampler.options.twirling.enable_gates = True
    t0 = time.time()
    job = sampler.run(isa)
    print("sampler job:", job.job_id()); res = job.result()
    out["sampler_job_id"] = job.job_id()
    rows = []
    for m, r in zip(meta, res):
        counts = r.join_data().get_counts()
        rows.append({**m, **analyse_counts(counts, RX, 15)})
    out["sampler"] = rows
    r1 = next(r for r in rows if not r["bleed"] and r["steps"] == 8 and r["fold"] == 1)
    r3 = next(r for r in rows if r["fold"] == 3)
    for key, se in (("raw", "raw_se"), ("postselected", "post_se")):
        out[f"zne_{key}"] = {"value": r1[key] + (r1[key] - r3[key]) / 2,
                             "se": float(np.hypot(1.5 * r1[se], 0.5 * r3[se]))}
    print(f"sampler done in {time.time() - t0:.0f} s wall")
    path = ROOT / "results" / f"hardware_{backend.name}{'_DRYRUN' if a.dry_run else ''}.json"
    json.dump(out, open(path, "w"), indent=1, default=float)          # save now: the sampler data is the core result

    # ---------------- Job 2: Estimator with IBM's built-in mitigation levels
    if a.with_estimator:
        nq = 15
        z = ["I"] * nq; z[nq - 1 - RX] = "Z"
        obs = SparsePauliOp("".join(z))
        est_rows = []
        for level in (0, 1, 2):
            opts = EstimatorOptions()
            opts.default_shots = EST_SHOTS
            opts.resilience_level = level
            if not a.dry_run and level > 0:
                opts.dynamical_decoupling.enable = True
                opts.dynamical_decoupling.sequence_type = "XY4"
            estimator = Estimator(mode=backend, options=opts)
            pubs = []
            for steps, qc in est:
                ic = pm.run(qc)
                pubs.append((ic, obs.apply_layout(ic.layout)))
            try:
                job = estimator.run(pubs)
                print(f"estimator level {level} job:", job.job_id())
                for (steps, _), pr in zip(est, job.result()):
                    ev = float(np.asarray(pr.data.evs)); sd = float(np.asarray(pr.data.stds))
                    est_rows.append({"resilience_level": level, "steps": steps, "energy": (1 - ev) / 2, "se": sd / 2,
                                     "job_id": job.job_id()})
            except Exception as e:      # local fake backends can't simulate TREX/ZNE at this size; keep going
                print(f"estimator level {level} failed: {type(e).__name__}: {str(e)[:200]}")
                est_rows.append({"resilience_level": level, "error": f"{type(e).__name__}: {str(e)[:300]}"})
        out["estimator"] = est_rows

    try:
        out["qpu_usage_seconds_reported"] = None if a.dry_run else job.usage()
    except Exception:
        pass
    json.dump(out, open(path, "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k not in ("sampler", "estimator")}, indent=1, default=float))
    for r in out["sampler"]:
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    for r in out.get("estimator", []):
        print(r)
    print("saved", path)


if __name__ == "__main__":
    main()
