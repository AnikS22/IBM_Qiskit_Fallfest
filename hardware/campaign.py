"""Full hardware test campaign: every experiment answers one question. Run all, or pick with --only.

  E1 trace      Does the real chip reproduce the sound wave arriving through the skull?   (main result)
                9 qubits, t = 0.5..3.0, readout correction + post-selection, x3 folds for ZNE.
                Pre-registered success: corrected within 2 SE of the ideal circuit at >= 5/6 times AND corr >= 0.9.
  E2 repeat     Is it reproducible? E1 twice more, with different transpiler seeds (often different physical qubits).
  E3 ablation   Which error-suppression setting helps? t = 1.5, 2.0 under {none, DD, twirling, DD+twirling}.
  E4 estimator  How does IBM's built-in mitigation (Estimator resilience 0/1/2: none / readout TREX / ZNE)
                compare with our physics-based post-selection? t = 1.5, 2.0.
  E5 size       How much does circuit size matter? Full 15-qubit line vs light-cone 9-qubit line, same physics.
  E6 2d         (stretch, only with --with-2d) A 2x2 grid with a skull cell on hardware: is 2D feasible today?

Usage
  python hardware/campaign.py --dry-run                     # free rehearsal of everything (FakeMarrakesh noise model)
  IBM_QUANTUM_TOKEN=... python hardware/campaign.py --backend ibm_marrakesh [--only E1,E3] [--max-seconds 900]
Outputs: results/hardware_campaign/<experiment>_<backend>.json (raw counts, settings, job ids, physical qubits,
calibration data of those qubits) and a summary printed at the end. Re-run analysis offline with --reanalyse.
"""
import argparse, json, os, sys, time, pathlib, warnings
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "hardware"))
warnings.filterwarnings("ignore", category=DeprecationWarning)
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qwave.grid import Grid
from qwave.hardware import ray_problem, fold
from qwave.circuits import unary_circuit
from qwave.classical import exact_receiver_energy
from qwave.subspace import trotter_receiver_energy
from qwave.readout import estimate
import run_ibm_v2 as v2

OUT = ROOT / "results" / "hardware_campaign"
SHOTS = int(os.environ.get("SHOTS", 4000))
PER_SHOT_S, PER_JOB_S = 0.00035, 2.0          # IBM rule of thumb (Open Plan docs); real usage is read back from jobs


# ------------------------------------------------------------------ helpers
def cal_circuits(n):
    c0 = QuantumCircuit(n); c0.measure_all()
    c1 = QuantumCircuit(n); c1.x(range(n)); c1.measure_all()
    return [c0, c1]


def ideal_and_exact(g, c, t, steps, rx, src=0):
    return (float(trotter_receiver_energy(g, c, t, steps, src, [rx])[0]),
            float(exact_receiver_energy(g, c, [t], src, [rx])[0, 0]))


def qubit_calibration(backend, isa):
    """Readout and 2-qubit error of the physical qubits actually used (for the documentation)."""
    try:
        layout = isa.layout.final_index_layout()
        tgt = backend.target
        ro = {q: tgt["measure"][(q,)].error for q in layout if tgt["measure"].get((q,)) is not None}
        cz = [tgt["cz"][e].error for e in tgt["cz"] if e[0] in layout and e[1] in layout and tgt["cz"][e] is not None]
        return {"physical_qubits": list(map(int, layout)), "readout_error": {int(k): v for k, v in ro.items()},
                "cz_error_median": float(np.median(cz)) if cz else None}
    except Exception as e:
        return {"error": str(e)[:200]}


class Runner:
    def __init__(self, backend, dry_run, max_seconds):
        self.backend, self.dry, self.max_s = backend, dry_run, max_seconds
        self.used_est = 0.0; self.used_reported = 0.0; self.jobs = []

    def budget_ok(self, shots_total, jobs=1):
        est = jobs * PER_JOB_S + shots_total * PER_SHOT_S
        if self.used_est + est > self.max_s:
            print(f"  ! skipping: would exceed --max-seconds ({self.used_est + est:.0f} > {self.max_s})"); return False
        self.used_est += est; return True

    def sampler(self, isa, dd=True, twirl=True, shots=SHOTS, seed=None):
        try:
            from qiskit_ibm_runtime.executor_sampler import Sampler
        except ImportError:
            from qiskit_ibm_runtime import SamplerV2 as Sampler
        s = Sampler(mode=self.backend); s.options.default_shots = shots
        if not self.dry:
            s.options.dynamical_decoupling.enable = dd
            s.options.twirling.enable_gates = twirl
            s.options.twirling.enable_measure = twirl
        job = s.run(isa); jid = job.job_id(); print("   job", jid, f"dd={dd} twirl={twirl}")
        res = job.result(); self._usage(job)
        out = []
        for r in res:
            try:
                out.append(r.join_data().get_counts())
            except AttributeError:
                out.append(r.data.meas.get_counts())
        self.jobs.append(jid)
        return jid, out

    def _usage(self, job):
        try:
            u = job.usage()
            if u: self.used_reported += float(u)
        except Exception:
            pass


# ------------------------------------------------------------------ experiments
def exp_trace(R, pm, tag, seed):
    g, c, steps, exact, ideal = v2.problem()
    n, circs, meta = v2.build(g, c, steps)
    if not R.budget_ok(len(circs) * SHOTS):
        return None
    pm_s = generate_preset_pass_manager(optimization_level=3, backend=R.backend, seed_transpiler=seed)
    isa = pm_s.run(circs)
    jid, counts = R.sampler(isa)
    rows, zne, verdict = v2.analyse(n, meta, isa, counts, exact, ideal)
    return {"experiment": tag, "job_id": jid, "seed": seed, "qubits": n, "shots": SHOTS, "verdict": verdict, "zne": zne,
            "rows": rows, "calibration": qubit_calibration(R.backend, isa[2]),
            "raw_counts": [{**m, "counts": cn} for m, cn in zip(meta, counts)]}


def exp_ablation(R, pm):
    g7, c7, _ = ray_problem(); g, c = Grid((4,)), c7[:4]; n = 9
    settings = [("none", False, False), ("DD", True, False), ("twirl", False, True), ("DD+twirl", True, True)]
    times = (1.5, 2.0)
    base = cal_circuits(n)
    for t in times:
        qc = unary_circuit(g, c, t, int(np.ceil(t / v2.DT)), 0); qc.measure_all(); base.append(qc)
    isa = pm.run(base)
    rows = []
    for name, dd, tw in settings:
        if not R.budget_ok(len(isa) * SHOTS):
            break
        jid, counts = R.sampler(isa, dd=dd, twirl=tw)
        for t, cn in zip(times, counts[2:]):
            ideal, exact = ideal_and_exact(g, c, t, int(np.ceil(t / v2.DT)), 2)
            rows.append({"setting": name, "t": t, "job_id": jid, "ideal_circuit": ideal, "exact": exact,
                         **estimate(cn, 2, n, counts[0], counts[1])})
        if R.dry:
            print("   (dry run: suppression settings are no-ops on a simulator; all four settings are equivalent)")
    return {"experiment": "E3_ablation", "rows": rows}


def exp_estimator(R, pm):
    from qiskit_ibm_runtime import EstimatorV2
    g7, c7, _ = ray_problem(); g, c = Grid((4,)), c7[:4]; n = 9
    z = ["I"] * n; z[n - 1 - 2] = "Z"; obs = SparsePauliOp("".join(z))
    times = (1.5, 2.0)
    pubs, refs = [], []
    for t in times:
        s = int(np.ceil(t / v2.DT)); ic = pm.run(unary_circuit(g, c, t, s, 0))
        pubs.append((ic, obs.apply_layout(ic.layout))); refs.append(ideal_and_exact(g, c, t, s, 2))
    rows = []
    for level in (0, 1, 2):
        mult = {0: 1, 1: 1.5, 2: 4}[level]
        if not R.budget_ok(len(pubs) * SHOTS * mult):
            break
        est = EstimatorV2(mode=R.backend); est.options.default_shots = SHOTS; est.options.resilience_level = level
        if not R.dry and level > 0:
            est.options.dynamical_decoupling.enable = True
        try:
            job = est.run(pubs); print("   estimator level", level, "job", job.job_id()); res = job.result(); R._usage(job)
            for t, (ideal, exact), pr in zip(times, refs, res):
                ev = float(np.asarray(pr.data.evs)); sd = float(np.asarray(pr.data.stds))
                rows.append({"resilience_level": level, "t": t, "energy": (1 - ev) / 2, "se": sd / 2,
                             "ideal_circuit": ideal, "exact": exact, "job_id": job.job_id()})
        except Exception as e:
            print("   estimator level", level, "failed:", str(e)[:200]); rows.append({"resilience_level": level, "error": str(e)[:300]})
    return {"experiment": "E4_estimator", "note": "Estimator has no post-selection; it measures P(receiver qubit = 1) directly",
            "rows": rows}


def exp_size(R, pm):
    times = (1.5, 2.0); rows = []
    g7, c7, _ = ray_problem()
    for cells in (7, 4):
        g, c = Grid((cells,)), c7[:cells]; n = g.n_vertices + g.n_edges
        circs = cal_circuits(n)
        for t in times:
            qc = unary_circuit(g, c, t, int(np.ceil(t / v2.DT)), 0); qc.measure_all(); circs.append(qc)
        if not R.budget_ok(len(circs) * SHOTS):
            break
        isa = pm.run(circs); jid, counts = R.sampler(isa)
        for t, cn, ic in zip(times, counts[2:], isa[2:]):
            ideal, exact = ideal_and_exact(g, c, t, int(np.ceil(t / v2.DT)), 2)
            rows.append({"cells": cells, "qubits": n, "t": t, "cz": int(ic.count_ops().get("cz", 0)), "job_id": jid,
                         "ideal_circuit": ideal, "exact": exact, **estimate(cn, 2, n, counts[0], counts[1])})
    return {"experiment": "E5_size", "rows": rows}


def exp_2d(R, pm):
    from qwave.phantom import SPEEDS, C_REF
    g = Grid((2, 2)); n = g.n_vertices + g.n_edges
    c = np.array([SPEEDS["scalp"], SPEEDS["skull"], SPEEDS["skull"], SPEEDS["brain"]]) / C_REF   # source corner -> skull -> brain corner
    rx = 3; rows = []
    circs = cal_circuits(n)
    for steps in (2, 4):
        qc = unary_circuit(g, c, 1.0, steps, 0); qc.measure_all(); circs.append(qc)
    if not R.budget_ok(len(circs) * SHOTS):
        return None
    isa = pm.run(circs); jid, counts = R.sampler(isa)
    for steps, cn, ic in zip((2, 4), counts[2:], isa[2:]):
        ideal, exact = ideal_and_exact(g, c, 1.0, steps, rx)
        rows.append({"steps": steps, "qubits": n, "cz": int(ic.count_ops().get("cz", 0)), "job_id": jid,
                     "ideal_circuit": ideal, "exact": exact, **estimate(cn, rx, n, counts[0], counts[1])})
    return {"experiment": "E6_2d", "grid": "2x2 (scalp, skull, skull, brain)", "rows": rows}


# ------------------------------------------------------------------ main
def summarise(results):
    print("\n================ SUMMARY ================")
    for r in results:
        if r is None:
            continue
        e = r["experiment"]
        if e.startswith("E1") or e.startswith("E2"):
            print(f"{e}: verdict {r['verdict']}")
            for x in r["rows"]:
                if x["fold"] == 1:
                    print(f"   t={x['t']:.1f} exact {x['exact']:.3f} ideal {x['ideal_circuit']:.3f} raw {x['raw']:.3f} "
                          f"post {x['postselected']:.3f} corrected {x['corrected']:.3f}±{x['corrected_se']:.3f} kept {x['kept_fraction']:.0%}")
        elif e == "E3_ablation":
            for x in r["rows"]:
                print(f"E3 {x['setting']:>9} t={x['t']}: corrected {x['corrected']:.3f}±{x['corrected_se']:.3f} (ideal {x['ideal_circuit']:.3f}) kept {x['kept_fraction']:.0%}")
        elif e == "E4_estimator":
            for x in r["rows"]:
                if "error" in x: print(f"E4 level {x['resilience_level']}: ERROR"); continue
                print(f"E4 level {x['resilience_level']} t={x['t']}: {x['energy']:.3f}±{x['se']:.3f} (ideal {x['ideal_circuit']:.3f})")
        elif e in ("E5_size", "E6_2d"):
            for x in r["rows"]:
                print(f"{e} {x.get('cells', '2x2')} cells/{x['qubits']}q {x.get('t', '')} cz={x['cz']}: corrected {x['corrected']:.3f}±{x['corrected_se']:.3f} "
                      f"(ideal {x['ideal_circuit']:.3f}) kept {x['kept_fraction']:.0%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--only", default="E1,E2,E3,E4,E5")
    ap.add_argument("--with-2d", action="store_true")
    ap.add_argument("--max-seconds", type=float, default=900)
    a = ap.parse_args()
    which = set(a.only.split(",")) | ({"E6"} if a.with_2d else set())
    backend = v2.get_backend(a.dry_run, a.backend)
    print(f"backend {backend.name}, shots {SHOTS}, experiments {sorted(which)}, budget {a.max_seconds:.0f} s (estimated)")
    R = Runner(backend, a.dry_run, a.max_seconds)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend, seed_transpiler=7)
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = backend.name + ("_DRYRUN" if a.dry_run else "")
    results = []
    plan = [("E1", lambda: exp_trace(R, pm, "E1_trace", 7)),
            ("E2", lambda: [exp_trace(R, pm, "E2_repeat_a", 11), exp_trace(R, pm, "E2_repeat_b", 23)]),
            ("E3", lambda: exp_ablation(R, pm)), ("E4", lambda: exp_estimator(R, pm)),
            ("E5", lambda: exp_size(R, pm)), ("E6", lambda: exp_2d(R, pm))]
    for key, fn in plan:
        if key not in which:
            continue
        print(f"\n--- {key} ---"); t0 = time.time()
        try:
            r = fn()
        except Exception as e:
            print(f"   {key} failed: {type(e).__name__}: {str(e)[:300]}"); r = {"experiment": key, "error": str(e)[:500]}
        for x in (r if isinstance(r, list) else [r]):
            if x is None:
                continue
            x.update(backend=backend.name, dry_run=a.dry_run, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            json.dump(x, open(OUT / f"{x['experiment']}_{suffix}.json", "w"), indent=1, default=float)
            results.append(x)
        print(f"   done in {time.time() - t0:.0f} s wall; estimated QPU so far {R.used_est:.0f} s"
              + (f", reported {R.used_reported:.0f} s" if R.used_reported else ""))
    summarise([r for r in results if "error" not in r])
    json.dump({"backend": backend.name, "jobs": R.jobs, "qpu_seconds_estimated": R.used_est,
               "qpu_seconds_reported": R.used_reported}, open(OUT / f"campaign_{suffix}.json", "w"), indent=1)
    print(f"\nall results in {OUT}")


if __name__ == "__main__":
    main()
