# Running the real IBM quantum hardware experiments

## Recommended: the full v2 campaign (one command, ~200 s estimated QPU, hard cap 900 s)

```bash
source venv/bin/activate
python hardware/campaign.py --dry-run --with-2d                    # free rehearsal (~15 min on a laptop)
export IBM_QUANTUM_TOKEN="your-api-key"
python hardware/campaign.py --backend ibm_marrakesh --with-2d      # real run; --only E1 to run just the main result
```
Results land in `results/hardware_campaign/`. Send the whole folder back. What each experiment tests is in
`EXPERIMENTS.md` §5. Keep the terminal open; each experiment waits in IBM's queue.

## v1 (already run on ibm_marrakesh): the single-file version below

The actual v1 job (`db9smd9gv2cc73e60pm0`) was submitted with `hardware/run_notebook03_hw.py`, which runs notebook 03's
`RUN_ON_IBM` cell (the same 6 circuits); `hardware/run_ibm.py` below is the standalone equivalent.

Needs: Python 3.10–3.13, internet, a free IBM Quantum account and API key (quantum.cloud.ibm.com).

```bash
# 1. set up (once)
python3 -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. check everything works (~30 s): should print "37 passed"
pytest -q

# 3. free rehearsal on IBM's simulated Kingston chip (~5 min, no QPU time used)
SHOTS=300 python hardware/run_ibm.py --dry-run          # Windows: set SHOTS=300 (cmd) / $env:SHOTS=300 (PowerShell)

# 4. the real run (~10-30 s of QPU time + queue wait)
export IBM_QUANTUM_TOKEN="your-api-key"                 # PowerShell: $env:IBM_QUANTUM_TOKEN="your-api-key"
# only if your account has several instances:
# export IBM_QUANTUM_INSTANCE="crn:..."
python hardware/run_ibm.py

# 5. optional: also compare IBM's built-in error mitigation (Estimator, resilience levels 0/1/2)
python hardware/run_ibm.py --with-estimator
```

What it does: 6 circuits on 15 qubits (the ear-to-ear sound wave through the 3D head phantom), 4,000 shots each,
with IBM dynamical decoupling and twirling. It then computes raw, post-selected and zero-noise-extrapolated results
against the exact classical answer (0.104).

Results are saved to `results/hardware_<chip>.json`. Keep the terminal open while the job waits in IBM's queue
(watch it under Workloads on quantum.cloud.ibm.com).

Simulated prediction (FakeKingston): raw ≈ 0.047, post-selected ≈ 0.096 ± 0.007, post-selected + ZNE ≈ 0.103 ± 0.011.

Never commit your API key; the script only reads it from the environment.
