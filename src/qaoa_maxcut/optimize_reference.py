"""Parameter optimization for the NumPy reference QAOA simulator."""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .problem import Edge, DEFAULT_EDGES, DEFAULT_N_NODES
from .reference_simulator import expected_cut


def optimize_qaoa(
    p: int = 1,
    steps: int = 250,
    restarts: int = 8,
    seed: int = 7,
    n_qubits: int = DEFAULT_N_NODES,
    edges: tuple[Edge, ...] = DEFAULT_EDGES,
) -> dict:
    """Find QAOA parameters by minimizing negative expected cut value.

    This uses derivative-free COBYLA to keep the teaching implementation
    straightforward.  Multi-start reduces dependence on one initial guess.
    """
    if p < 1 or steps < 1 or restarts < 1:
        raise ValueError("p, steps and restarts must all be positive")

    rng = np.random.default_rng(seed)
    best = None
    history = []

    def objective(parameters: np.ndarray) -> float:
        gammas = parameters[:p]
        betas = parameters[p:]
        return -expected_cut(gammas, betas, n_qubits, edges)

    for restart in range(restarts):
        initial = np.concatenate([
            rng.uniform(0.05, np.pi - 0.05, size=p),
            rng.uniform(0.05, (np.pi / 2) - 0.05, size=p),
        ])
        result = minimize(
            objective,
            initial,
            method="COBYLA",
            options={"maxiter": steps, "rhobeg": 0.4, "tol": 1e-5},
        )
        expected = -float(result.fun)
        record = {
            "restart": restart + 1,
            "expected_cut": expected,
            "gammas": [float(value) for value in result.x[:p]],
            "betas": [float(value) for value in result.x[p:]],
            "optimizer_success": bool(result.success),
            "optimizer_message": str(result.message),
        }
        history.append(record)
        if best is None or expected > best["expected_cut"]:
            best = record

    assert best is not None
    best_result = dict(best)
    best_result["restart_history"] = [dict(item) for item in history]
    best_result["p"] = p
    best_result["steps_per_restart"] = steps
    best_result["restarts"] = restarts
    return best_result
