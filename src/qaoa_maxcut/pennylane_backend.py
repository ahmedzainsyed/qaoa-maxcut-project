"""QAOA implementation using PennyLane's default.qubit simulator.

The training QNode uses exact expectation values.  A second finite-shot QNode
samples candidate bitstrings after the parameters have been optimized.
"""
from __future__ import annotations

import numpy as np


def run_pennylane(
    edges: tuple[tuple[int, int, float], ...],
    n_qubits: int,
    p: int = 1,
    steps: int = 150,
    restarts: int = 4,
    shots: int = 5000,
    seed: int = 7,
) -> dict:
    try:
        import pennylane as qml
        from pennylane import numpy as pnp
    except ImportError as exc:
        raise RuntimeError(
            "PennyLane is not installed. Activate your virtual environment and run: "
            "python -m pip install -r requirements.txt"
        ) from exc

    if p < 1 or steps < 1 or restarts < 1 or shots < 1:
        raise ValueError("p, steps, restarts and shots must all be positive")

    # C = sum_edges w * (I - Z_i Z_j)/2, whose measured value is cut weight.
    coefficients = []
    observables = []
    for i, j, weight in edges:
        coefficients.extend([weight / 2.0, -weight / 2.0])
        observables.extend([qml.Identity(0), qml.PauliZ(i) @ qml.PauliZ(j)])
    cost_hamiltonian = qml.Hamiltonian(coefficients, observables)

    exact_device = qml.device("default.qubit", wires=n_qubits)

    def apply_qaoa_layers(parameters):
        gammas = parameters[:p]
        betas = parameters[p:]
        for wire in range(n_qubits):
            qml.Hadamard(wires=wire)
        for layer in range(p):
            # IsingZZ(phi) = exp(-i*phi*Z_i*Z_j/2).
            # phi=-gamma*w implements the ZZ part of exp(-i*gamma*C).
            # The missing identity contribution is only a global phase.
            for i, j, weight in edges:
                qml.IsingZZ(-gammas[layer] * weight, wires=[i, j])
            # RX(2*beta) = exp(-i*beta*X), the standard QAOA mixer.
            for wire in range(n_qubits):
                qml.RX(2.0 * betas[layer], wires=wire)

    @qml.qnode(exact_device)
    def expected_cut_qnode(parameters):
        apply_qaoa_layers(parameters)
        return qml.expval(cost_hamiltonian)

    def objective(parameters):
        return -expected_cut_qnode(parameters)

    rng = np.random.default_rng(seed)
    best = None
    restart_history = []

    for restart in range(restarts):
        initial = np.concatenate([
            rng.uniform(0.05, np.pi - 0.05, size=p),
            rng.uniform(0.05, np.pi / 2.0 - 0.05, size=p),
        ])
        parameters = pnp.array(initial, requires_grad=True)
        optimizer = qml.AdamOptimizer(stepsize=0.05)
        for _ in range(steps):
            parameters = optimizer.step(objective, parameters)
        expected = float(expected_cut_qnode(parameters))
        record = {
            "restart": restart + 1,
            "expected_cut": expected,
            "gammas": [float(value) for value in parameters[:p]],
            "betas": [float(value) for value in parameters[p:]],
        }
        restart_history.append(record)
        if best is None or expected > best["expected_cut"]:
            best = record

    assert best is not None
    best_parameters = pnp.array(best["gammas"] + best["betas"], requires_grad=False)
    sampling_device = qml.device("default.qubit", wires=n_qubits, shots=shots, seed=seed)

    @qml.qnode(sampling_device)
    def sample_qnode(parameters):
        apply_qaoa_layers(parameters)
        return qml.sample(wires=range(n_qubits))

    raw_samples = np.asarray(sample_qnode(best_parameters), dtype=int)
    if raw_samples.ndim == 1:
        raw_samples = raw_samples.reshape(1, -1)
    counts: dict[str, int] = {}
    for row in raw_samples:
        bitstring = "".join(str(int(bit)) for bit in row)
        counts[bitstring] = counts.get(bitstring, 0) + 1

    best_result = dict(best)
    best_result["restart_history"] = [dict(item) for item in restart_history]
    best_result["p"] = p
    best_result["steps_per_restart"] = steps
    best_result["restarts"] = restarts
    best_result["shots"] = shots
    best_result["counts"] = counts
    best_result["framework"] = f"PennyLane {qml.__version__} / default.qubit"
    return best_result
