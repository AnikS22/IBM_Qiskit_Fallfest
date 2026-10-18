#!/bin/bash
# Stride classical FWI baseline: input -> forward (synthetic data) -> invert. 2D first, then 3D. Run from repo root.
PY=.venv-stride/bin/python
export SDKROOT=$(xcrun --show-sdk-path) DEVITO_ARCH=gcc-15 DEVITO_LANGUAGE=openmp  # Apple clang lacks OpenMP
unset $(env | grep -o '^MOSAIC_ARTIFACT_[^=]*')
for d in 2 3; do
  R=runs/stride_${d}d; mkdir -p $R
  echo "=== stride ${d}D input $(date +%T)"
  $PY -m classical.make_stride_input --dimension $d --output $R/input.npz --execute || { echo "FAIL input ${d}D"; continue; }
  echo "--- stride ${d}D forward $(date +%T)"
  $PY -m classical.stride_baseline forward --input $R/input.npz --config classical/configs/stride.json --output $R/forward --execute || { echo "FAIL forward ${d}D"; continue; }
  echo "--- stride ${d}D invert $(date +%T)"
  $PY -m classical.stride_baseline invert --input $R/forward/inversion_input.npz --config classical/configs/stride.json --output $R/invert --execute || echo "FAIL invert ${d}D"
done
echo "=== STRIDE DONE $(date +%T)"
