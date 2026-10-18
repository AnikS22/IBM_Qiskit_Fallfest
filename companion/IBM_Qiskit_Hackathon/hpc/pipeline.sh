#!/bin/bash
# Usage (repo root): CONFIGS="matched_2d" NOISE=0.001 STRIDE_DIMS="3" bash hpc/pipeline.sh
# Per config: observations -> classical -> Aer ideal -> Aer noisy. Then Stride input -> forward -> invert.
CONFIGS=${CONFIGS-"small_1d pulse_1d matched_2d"}; NOISE=${NOISE:-0.001}; STRIDE_DIMS=${STRIDE_DIMS-"2 3"}
PY=.venv/bin/python; SPY=.venv-stride/bin/python; mkdir -p runs
for cfg in $CONFIGS; do
  C=classical/configs/$cfg.json; R=runs/$cfg; O=$R/obs/observations.npz
  echo "=== $cfg $(date +%T)"
  [ -f $O ] || $PY -m classical.make_observations --config $C --output $R/obs --execute || { echo "FAIL obs $cfg"; continue; }
  [ -d $R/classical ] || $PY -m classical.run --config $C --observations $O --output $R/classical --execute || echo "FAIL classical $cfg"
  [ -d $R/aer_ideal ] || $PY -m simulator.run --config $C --observations $O --output $R/aer_ideal --execute || echo "FAIL aer_ideal $cfg"
  [ -d $R/aer_noisy ] || $PY -m simulator.run --config $C --observations $O --output $R/aer_noisy --execute --noise-probability $NOISE || echo "FAIL aer_noisy $cfg"
done
for d in $STRIDE_DIMS; do
  R=runs/stride_${d}d; mkdir -p $R; echo "=== stride ${d}D $(date +%T)"
  [ -f $R/input.npz ] || $SPY -m classical.make_stride_input --dimension $d --output $R/input.npz --execute || continue
  [ -d $R/forward ] || $SPY -m classical.stride_baseline forward --input $R/input.npz --config classical/configs/stride.json --output $R/forward --execute || continue
  [ -d $R/invert ] || $SPY -m classical.stride_baseline invert --input $R/forward/inversion_input.npz --config classical/configs/stride.json --output $R/invert --execute || echo "FAIL invert ${d}D"
done
echo "=== DONE $(date +%T)"
