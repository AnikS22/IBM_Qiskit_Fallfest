"""Output is created only by an explicitly authorized CLI invocation."""
from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys
import time
import numpy as np


@dataclass
class Prediction:
    """Forward-model output on the trace grid (sources, times, receivers), in Pa:
    mean pressure, reporting standard error, and unbiased sampling variance of the mean."""
    mean: np.ndarray
    standard_error: np.ndarray
    # Unbiased estimator of Var(mean), distinct from the reporting SE floor.
    sampling_variance: np.ndarray


class Evidence:
    """One run directory. Creating it fails if the path exists, then records a manifest
    (engine, Python and package versions, SHA-256 of every source file), a source snapshot,
    the config and, if given, the observations."""
    def __init__(self, directory, config_path, engine, observations=None):
        self.path = Path(directory).resolve()
        self.path.mkdir(parents=True, exist_ok=False)
        self.started = time.perf_counter()
        root = Path(__file__).resolve().parents[2]
        versions = {}
        for name in ('numpy', 'scipy', 'stride', 'devito', 'qiskit', 'qiskit-aer',
                     'qiskit-ibm-runtime'):
            try:
                versions[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                pass
        files = [p for package in ('classical', 'simulator', 'ibm_hardware')
                 for p in (root/package).rglob('*.py')]
        hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        for source in files:
            destination = self.path/'source'/source.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        self.write('manifest.json', {'engine': engine, 'python': sys.version, 'versions': versions,
                                    'source_sha256': hashes, 'status': 'started'})
        shutil.copyfile(config_path, self.path/'config.json')
        if observations is not None:
            shutil.copyfile(observations, self.path/'observations.npz')

    def write(self, name, value):
        """Write `value` as JSON to `name` in the run directory atomically (temp file, then rename)."""
        target = self.path/name
        temp = target.with_suffix(target.suffix+'.tmp')
        temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
        temp.replace(target)

    def finish(self, statistics):
        """Write completed.json with the wall-clock time since start plus the solver statistics."""
        self.write('completed.json', {'wall_seconds': time.perf_counter()-self.started, **statistics})
