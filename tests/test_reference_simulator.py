import numpy as np

from qaoa_maxcut.problem import DEFAULT_EDGES, DEFAULT_N_NODES
from qaoa_maxcut.reference_simulator import (
    expected_cut,
    prepare_qaoa_state,
    probability_distribution,
    sample_counts,
)


def test_statevector_is_normalized():
    state = prepare_qaoa_state([0.3], [0.2], DEFAULT_N_NODES, DEFAULT_EDGES)
    assert np.isclose(np.sum(np.abs(state) ** 2), 1.0)


def test_zero_layer_distribution_is_uniform():
    distribution = probability_distribution([], [], DEFAULT_N_NODES, DEFAULT_EDGES)
    assert len(distribution) == 16
    assert all(np.isclose(probability, 1.0 / 16.0) for probability in distribution.values())
    assert np.isclose(expected_cut([], [], DEFAULT_N_NODES, DEFAULT_EDGES), 2.5)


def test_sampling_returns_requested_number_of_shots():
    distribution = {"00": 0.5, "01": 0.5}
    counts = sample_counts(distribution, shots=250, seed=11)
    assert sum(counts.values()) == 250
    assert set(counts).issubset(distribution)
