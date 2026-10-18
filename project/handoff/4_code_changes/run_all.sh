#!/bin/bash
# Local pipeline per config: observations -> classical -> Aer noiseless -> Aer noisy. Run from repo root.
PY=.venv/bin/python
NOISE=${NOISE:-0.001}
mkdir -p runs
for cfg in small_1d pulse_1d matched_2d; do
  C=classical/configs/$cfg.json; R=runs/$cfg
  echo "=== $cfg $(date +%T)"
  $PY -m classical.make_observations --config $C --output $R/obs --execute || { echo "FAIL obs $cfg"; continue; }
  O=$R/obs/observations.npz
  $PY -m classical.run --config $C --observations $O --output $R/classical --execute || echo "FAIL classical $cfg"
  echo "--- $cfg aer ideal $(date +%T)"
  $PY -m simulator.run --config $C --observations $O --output $R/aer_ideal --execute || echo "FAIL aer_ideal $cfg"
  echo "--- $cfg aer noisy p=$NOISE $(date +%T)"
  $PY -m simulator.run --config $C --observations $O --output $R/aer_noisy --execute --noise-probability $NOISE || echo "FAIL aer_noisy $cfg"
done
echo "=== DONE $(date +%T)"
