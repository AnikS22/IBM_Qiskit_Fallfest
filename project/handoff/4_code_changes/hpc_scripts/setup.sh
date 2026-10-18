#!/bin/bash
# One-time env setup on a Linux HPC login node. Run from repo root: bash hpc/setup.sh
set -e
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv venv -q -p 3.13 .venv && uv pip install -q -p .venv/bin/python -r simulator/requirements.txt
# Stride's C extension needs Python <=3.10; its devito pin clashes with classical's numpy pin.
uv venv -q -p 3.10 .venv-stride && uv pip install -q -p .venv-stride/bin/python -r classical/requirements-stride.txt
.venv/bin/python -c "import qiskit_aer; print('aer ok')"
.venv-stride/bin/python -c "import stride, devito; print('stride ok')"
