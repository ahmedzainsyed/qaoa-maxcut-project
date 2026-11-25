from qaoa_maxcut.problem import (
    DEFAULT_EDGES,
    DEFAULT_N_NODES,
    DEFAULT_PROBLEM,
    cut_value,
    exhaustive_search,
    ising_cut_value,
    qubo_energy,
)


def test_known_partition_has_four_cut_edges():
    assert cut_value("0101", DEFAULT_EDGES) == 4.0


def test_qubo_energy_is_negative_cut_value():
    for bits in ("0000", "0001", "0101", "1111"):
        assert qubo_energy(bits, DEFAULT_EDGES) == -cut_value(bits, DEFAULT_EDGES)


def test_ising_and_binary_formulations_agree():
    for integer in range(2**DEFAULT_N_NODES):
        bits = format(integer, f"0{DEFAULT_N_NODES}b")
        assert ising_cut_value(bits, DEFAULT_EDGES) == cut_value(bits, DEFAULT_EDGES)


def test_exhaustive_optimum_is_four():
    result = exhaustive_search(DEFAULT_N_NODES, DEFAULT_EDGES)
    assert result["n_assignments_checked"] == 16
    assert result["optimal_cut_value"] == 4.0
    assert "0101" in result["optimal_bitstrings"]
    assert "1010" in result["optimal_bitstrings"]


def test_problem_object_encapsulates_graph_and_evaluation():
    assert DEFAULT_PROBLEM.evaluate("0101") == 4.0
    assert DEFAULT_PROBLEM.solve_exactly()["optimal_cut_value"] == 4.0
