"""Actual Aer execution of decomposed circuits, with an auditable signed-pressure readout."""
import os
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from classical._core.evidence import Prediction
from .readout import ancilla_statistics
from .circuits import pauli_terms, evolution, pressure_interferometer


def _simulate(job):
    """Compile and run one circuit in a worker process; fixed per-circuit seed keeps results order-independent."""
    (n, terms, duration, max_step, source, receiver), seed, run_seed, shots, noise_probability, max_gates = job
    # Built here, not in the parent: multi-million-gate circuits are too big to pickle around.
    qc = pressure_interferometer(evolution(n, terms, duration, max_step), source, receiver)
    compiled = transpile(qc, basis_gates=['rz', 'sx', 'x', 'cx'], optimization_level=1, seed_transpiler=seed)
    if compiled.size() > max_gates:
        raise RuntimeError('Compiled circuit exceeds gate limit')
    noise = None
    if noise_probability:
        noise = NoiseModel()
        noise.add_all_qubit_quantum_error(depolarizing_error(noise_probability, 1), ['h', 'x', 'rz', 'sx'])
        noise.add_all_qubit_quantum_error(depolarizing_error(noise_probability, 2), ['cx'])
    sim = AerSimulator(method='density_matrix' if noise else 'statevector', noise_model=noise,
                       max_parallel_threads=1)
    result = sim.run(compiled, shots=shots, seed_simulator=run_seed).result()
    if not result.success:
        raise RuntimeError(f'Aer failed: {result.status}')
    return result.get_counts(), compiled.depth(), compiled.size(), dict(compiled.count_ops())


class GateForward:
    """Forward solver that runs every source/time/receiver circuit on Aer, ideal or with generic
    depolarizing noise, within circuit, shot, qubit and gate budgets."""
    def __init__(self, problem, evidence, shots, seed, max_circuits, max_total_shots,
                 max_data_qubits=7, max_gates=500000, noise_probability=0.0):
        if shots < 2 or max_circuits < 1 or max_total_shots < shots:
            raise ValueError('Invalid execution budget')
        if not 0 <= noise_probability <= 0.1:
            raise ValueError('Generic depolarizing probability must be in [0, 0.1]')
        n = int(np.ceil(np.log2(problem.grid.n_vertices+problem.grid.n_edges)))
        if n > min(max_data_qubits, 8):
            raise ValueError('Problem exceeds compact compilation register limit')
        noise = None
        if noise_probability:
            noise = NoiseModel()
            # Stress model only; not calibrated IBM device noise.
            noise.add_all_qubit_quantum_error(depolarizing_error(noise_probability, 1), ['h', 'x', 'rz', 'sx'])
            noise.add_all_qubit_quantum_error(depolarizing_error(noise_probability, 2), ['cx'])
        # Noisy statevector re-simulates per shot; <=9 qubits, so the exact density matrix is cheaper.
        self.simulator = AerSimulator(method='density_matrix' if noise else 'statevector', noise_model=noise)
        self.problem, self.evidence = problem, evidence
        self.shots, self.seed = int(shots), int(seed)
        self.max_circuits, self.max_total_shots = int(max_circuits), int(max_total_shots)
        self.max_data_qubits, self.max_gates = max_data_qubits, max_gates
        self.calls = self.circuits = self.total_shots = 0
        self.max_observed_depth = self.max_observed_gates = 0
        self.noise_probability = noise_probability

    def predict(self, parameters):
        """Simulate one forward call (circuits run in parallel worker processes) and return pressure traces
        (Pa) with shot-noise errors; saves each circuit's counts to the run directory."""
        p = self.problem
        needed = len(p.sources)*len(p.receivers)*sum(len(p.impulses(t)) for t in p.times)
        if self.circuits+needed > self.max_circuits or self.total_shots+needed*self.shots > self.max_total_shots:
            raise RuntimeError('Forward call would exceed total circuit/shot budget; no part of this call was submitted')
        n, terms = pauli_terms(p.hamiltonian(parameters), self.max_data_qubits)
        c = p.speeds(parameters)
        output, variance = np.zeros(p.trace_shape), np.zeros(p.trace_shape)
        sampling_variance = np.zeros(p.trace_shape)
        call = self.calls
        self.calls += 1
        jobs, meta = [], []
        for si, source in enumerate(p.sources):
            for ti, time in enumerate(p.times):
                for duration, pressure_increment in p.impulses(time):
                    # Each distinct pulse contribution is separately prepared and measured.
                    for ri, receiver in enumerate(p.receivers):
                        qc = (n, terms, duration, p.config['trotter_step_s'], int(source), int(receiver))
                        index = self.circuits
                        run_seed = (self.seed+index) % (2**32-1)
                        self.circuits += 1
                        self.total_shots += self.shots
                        jobs.append((qc, self.seed, run_seed, self.shots, self.noise_probability, self.max_gates))
                        meta.append((si, ti, ri, int(source), int(receiver), time, duration, pressure_increment, index, run_seed))
        # ponytail: one pool per forward call; workers = cores (QWAVE_WORKERS overrides).
        workers = int(os.environ.get('QWAVE_WORKERS', os.cpu_count()))
        with ProcessPoolExecutor(max_workers=min(workers, len(jobs))) as pool:
            results = list(pool.map(_simulate, jobs))
        for (si, ti, ri, source, receiver, time, duration, pressure_increment, index, run_seed), \
                (counts, depth, gates, ops) in zip(meta, results):
            self.max_observed_depth = max(self.max_observed_depth, depth)
            self.max_observed_gates = max(self.max_observed_gates, gates)
            total = self.shots
            overlap, se, overlap_variance = ancilla_statistics(counts, total)
            scale = pressure_increment*c[receiver]/c[source]
            output[si, ti, ri] += scale*overlap
            variance[si, ti, ri] += (scale*se)**2
            # Sample variance / N for independent +/-1 measurements.
            # Unlike the smoothed SE, this gives an unbiased loss correction.
            sampling_variance[si, ti, ri] += scale**2*overlap_variance
            self.evidence.write(f'counts_{index:07d}.json', {
                'forward_call': call, 'parameters': np.asarray(parameters).tolist(),
                'source': source, 'receiver': receiver, 'time_s': float(time),
                'evolution_time_s': float(duration), 'physical_scale_pa': float(scale),
                'counts': counts, 'shots': total, 'seed_simulator': run_seed,
                'signed_overlap': overlap, 'overlap_standard_error': float(se),
                'unbiased_overlap_variance': float(overlap_variance),
                'data_qubits': n, 'ancillas': 1, 'depth': depth,
                'gates': gates, 'operations': ops,
                'pauli_terms': len(terms)})
        return Prediction(output, np.sqrt(variance), sampling_variance)

    def statistics(self):
        """Run counters, maximum depth and gate count, and the noise setting, for completed.json."""
        return {'forward_calls': self.calls, 'circuits': self.circuits, 'shots': self.total_shots,
                'maximum_depth': self.max_observed_depth, 'maximum_gates': self.max_observed_gates,
                'noise': 'ideal' if self.noise_probability == 0 else 'generic_depolarizing_stress',
                'noise_probability': self.noise_probability,
                'gradient': 'classical finite differences of gate-sampled pressure loss'}
