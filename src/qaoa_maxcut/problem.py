"""Classical definition and verification tools for the Max-Cut problem.

This module deliberately has no quantum-framework dependency.  It defines the
problem once so both the reference simulator and PennyLane implementation use
exactly the same objective.
"""
from __future__ import annotations

from itertools import product
from typing import Iterable, Sequence

Edge = tuple[int, int, float]

# Four monitoring nodes and five weighted connections.
# This graph is intentionally small so we can verify the exact answer by
# checking all 2**4 = 16 possible partitions.
DEFAULT_EDGES: tuple[Edge, ...] = (
    (0, 1, 1.0),
    (1, 2, 1.0),
    (2, 3, 1.0),
    (3, 0, 1.0),
    (0, 2, 1.0),
)
DEFAULT_N_NODES = 4


def normalize_bitstring(bits: str | Sequence[int], n_nodes: int) -> tuple[int, ...]:
    """Validate and normalize a partition as a tuple of 0/1 values."""
    if isinstance(bits, str):
        cleaned = bits.strip().replace(" ", "")
        if len(cleaned) != n_nodes or any(ch not in "01" for ch in cleaned):
            raise ValueError(f"Expected a {n_nodes}-character 0/1 bitstring; got {bits!r}")
        values = tuple(int(ch) for ch in cleaned)
    else:
        values = tuple(int(value) for value in bits)
        if len(values) != n_nodes or any(value not in (0, 1) for value in values):
            raise ValueError(f"Expected {n_nodes} binary values; got {bits!r}")
    return values


def cut_value(bits: str | Sequence[int], edges: Iterable[Edge] = DEFAULT_EDGES) -> float:
    """Return the total weight of edges whose endpoints are in different sets."""
    edge_list = tuple(edges)
    n_nodes = 1 + max(max(i, j) for i, j, _ in edge_list)
    assignment = normalize_bitstring(bits, n_nodes)
    return sum(weight for i, j, weight in edge_list if assignment[i] != assignment[j])


def exhaustive_search(
    n_nodes: int = DEFAULT_N_NODES,
    edges: Iterable[Edge] = DEFAULT_EDGES,
) -> dict:
    """Find the exact Max-Cut answer by enumerating all binary assignments.

    This is deliberately a small-instance benchmark, not a scalable algorithm.
    """
    edge_list = tuple(edges)
    scored = []
    for bits in product((0, 1), repeat=n_nodes):
        string = "".join(str(bit) for bit in bits)
        scored.append((string, cut_value(bits, edge_list)))

    best_value = max(score for _, score in scored)
    best_strings = [string for string, score in scored if score == best_value]
    return {
        "n_nodes": n_nodes,
        "n_assignments_checked": 2**n_nodes,
        "optimal_cut_value": float(best_value),
        "optimal_bitstrings": best_strings,
        "all_scores": scored,
    }


def qubo_energy(bits: str | Sequence[int], edges: Iterable[Edge] = DEFAULT_EDGES) -> float:
    """QUBO energy for the minimization form of Max-Cut: E(x) = -cut(x)."""
    return -cut_value(bits, edges)


def ising_cut_value(bits: str | Sequence[int], edges: Iterable[Edge] = DEFAULT_EDGES) -> float:
    """Evaluate sum w_ij * (1 - s_i*s_j)/2 with spins s_i = 1 - 2*x_i."""
    edge_list = tuple(edges)
    n_nodes = 1 + max(max(i, j) for i, j, _ in edge_list)
    assignment = normalize_bitstring(bits, n_nodes)
    spins = tuple(1 - 2 * value for value in assignment)
    return sum(weight * (1 - spins[i] * spins[j]) / 2 for i, j, weight in edge_list)


def partition_label(bits: str | Sequence[int]) -> str:
    """Human-readable A/B assignment (0 -> A, 1 -> B)."""
    if isinstance(bits, str):
        values = tuple(int(ch) for ch in bits)
    else:
        values = tuple(int(value) for value in bits)
    group_a = [f"Node {i}" for i, value in enumerate(values) if value == 0]
    group_b = [f"Node {i}" for i, value in enumerate(values) if value == 1]
    return f"Group A: {', '.join(group_a) or '(none)'} | Group B: {', '.join(group_b) or '(none)'}"


def random_cut_expectation(edges: Iterable[Edge] = DEFAULT_EDGES) -> float:
    """Expected cut weight of a uniformly random binary partition."""
    return 0.5 * sum(weight for _, _, weight in edges)

# Small object-oriented wrapper: the graph and its operations travel together.
# This demonstrates encapsulation without hiding the simple mathematics above.
from dataclasses import dataclass


@dataclass(frozen=True)
class MaxCutProblem:
    """An immutable Max-Cut instance, represented as an edge list."""
    n_nodes: int
    edges: tuple[Edge, ...]

    def __post_init__(self) -> None:
        if self.n_nodes < 2:
            raise ValueError("A Max-Cut problem needs at least two nodes")
        for i, j, weight in self.edges:
            if i == j or i < 0 or j < 0 or i >= self.n_nodes or j >= self.n_nodes:
                raise ValueError(f"Invalid edge: {(i, j, weight)}")
            if weight < 0:
                raise ValueError("Edge weights must be non-negative")

    def evaluate(self, bitstring: str | Sequence[int]) -> float:
        return cut_value(bitstring, self.edges)

    def solve_exactly(self) -> dict:
        return exhaustive_search(self.n_nodes, self.edges)


DEFAULT_PROBLEM = MaxCutProblem(DEFAULT_N_NODES, DEFAULT_EDGES)
