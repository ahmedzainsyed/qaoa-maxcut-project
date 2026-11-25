"""Small, transparent state-vector reference simulator for QAOA.

Purpose: make the state preparation, cost phase and mixer understandable and
provide an implementation independent of PennyLane for cross-checking.
It is a teaching/reference simulator, not a production quantum simulator.
"""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np

from .problem import Edge, DEFAULT_EDGES, DEFAULT_N_NODES, cut_value


def _bits_for_index(index: int, n_qubits: int) -> tuple[int, ...]:
    """Use wire 0 as the left-most bit, matching printed bitstrings."""
    return tuple((index >> (n_qubits - 1 - wire)) & 1 for wire in range(n_qubits))


def _apply_hadamard_all(state: np.ndarray, n_qubits: int) -> np.ndarray:
    """Apply H to every qubit using pairwise amplitude updates."""
    result = state.copy()
    scale = 1.0 / math.sqrt(2.0)
    dimension = len(result)
    for wire in range(n_qubits):
        mask = 1 << (n_qubits - 1 - wire)
        for base in range(dimension):
            if base & mask == 0:
                other = base | mask
                a0, a1 = result[base], result[other]
                result[base] = (a0 + a1) * scale
                result[other] = (a0 - a1) * scale
    return result


def _apply_rx_all(state: np.ndarray, beta: float, n_qubits: int) -> np.ndarray:
    """Apply RX(2*beta) to every qubit; RX(2b)=cos(b)I-i*sin(b)X."""
    result = state.copy()
    cosine, sine = math.cos(beta), -1j * math.sin(beta)
    dimension = len(result)
    for wire in range(n_qubits):
        mask = 1 << (n_qubits - 1 - wire)
        for base in range(dimension):
            if base & mask == 0:
                other = base | mask
                a0, a1 = result[base], result[other]
                result[base] = cosine * a0 + sine * a1
                result[other] = sine * a0 + cosine * a1
    return result


def prepare_qaoa_state(
    gammas: Iterable[float],
    betas: Iterable[float],
    n_qubits: int = DEFAULT_N_NODES,
    edges: Iterable[Edge] = DEFAULT_EDGES,
) -> np.ndarray:
    """Prepare the QAOA state for the given p-layer parameters."""
    gamma_values = tuple(float(value) for value in gammas)
    beta_values = tuple(float(value) for value in betas)
    if len(gamma_values) != len(beta_values):
        raise ValueError("gammas and betas must have the same number of layers")

    edge_list = tuple(edges)
    state = np.zeros(2**n_qubits, dtype=np.complex128)
    state[0] = 1.0
    state = _apply_hadamard_all(state, n_qubits)

    # C(x) is the total cut weight.  It is diagonal in the computational basis,
    # so the cost unitary multiplies each basis amplitude by exp(-i*gamma*C(x)).
    for gamma, beta in zip(gamma_values, beta_values):
        for index in range(len(state)):
            bits = _bits_for_index(index, n_qubits)
            state[index] *= np.exp(-1j * gamma * cut_value(bits, edge_list))
        state = _apply_rx_all(state, beta, n_qubits)

    return state


def expected_cut(
    gammas: Iterable[float],
    betas: Iterable[float],
    n_qubits: int = DEFAULT_N_NODES,
    edges: Iterable[Edge] = DEFAULT_EDGES,
) -> float:
    """Calculate the exact expectation of the cut objective."""
    state = prepare_qaoa_state(gammas, betas, n_qubits, edges)
    probabilities = np.abs(state) ** 2
    values = np.array(
        [cut_value(_bits_for_index(i, n_qubits), edges) for i in range(len(state))],
        dtype=float,
    )
    return float(np.dot(probabilities, values))


def probability_distribution(
    gammas: Iterable[float],
    betas: Iterable[float],
    n_qubits: int = DEFAULT_N_NODES,
    edges: Iterable[Edge] = DEFAULT_EDGES,
) -> dict[str, float]:
    """Return the exact computational-basis probability distribution."""
    state = prepare_qaoa_state(gammas, betas, n_qubits, edges)
    probabilities = np.abs(state) ** 2
    return {
        format(index, f"0{n_qubits}b"): float(probability)
        for index, probability in enumerate(probabilities)
    }


def sample_counts(
    probabilities: dict[str, float],
    shots: int = 5000,
    seed: int = 7,
) -> dict[str, int]:
    """Sample bitstrings from a statevector probability distribution."""
    if shots < 1:
        raise ValueError("shots must be at least 1")
    bitstrings = list(probabilities)
    values = np.array([probabilities[key] for key in bitstrings], dtype=float)
    values /= values.sum()
    rng = np.random.default_rng(seed)
    samples = rng.choice(len(bitstrings), size=shots, p=values)
    unique, counts = np.unique(samples, return_counts=True)
    return {bitstrings[int(index)]: int(count) for index, count in zip(unique, counts)}
