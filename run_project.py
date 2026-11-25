"""Command-line entry point for the QAOA Max-Cut project."""
from __future__ import annotations

import argparse
from pathlib import Path

from qaoa_maxcut.problem import (
    DEFAULT_EDGES,
    DEFAULT_N_NODES,
    exhaustive_search,
    random_cut_expectation,
)
from qaoa_maxcut.optimize_reference import optimize_qaoa
from qaoa_maxcut.reference_simulator import probability_distribution, sample_counts
from qaoa_maxcut.reporting import build_summary, save_outputs

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Solve a four-node Max-Cut example with QAOA."
    )
    parser.add_argument(
        "--backend",
        choices=["pennylane", "numpy"],
        default="pennylane",
        help="PennyLane circuit or transparent NumPy reference simulator",
    )
    parser.add_argument("--p", type=int, default=1, help="QAOA layer depth")
    parser.add_argument("--steps", type=int, default=150, help="optimizer steps per restart")
    parser.add_argument("--restarts", type=int, default=4, help="independent initializations")
    parser.add_argument("--shots", type=int, default=5000, help="measurement repetitions")
    parser.add_argument("--seed", type=int, default=7, help="random seed")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "outputs", help="directory for generated JSON/CSV"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if min(args.p, args.steps, args.restarts, args.shots) < 1:
        raise SystemExit("--p, --steps, --restarts and --shots must all be positive")

    exact = exhaustive_search(DEFAULT_N_NODES, DEFAULT_EDGES)

    if args.backend == "pennylane":
        from qaoa_maxcut.pennylane_backend import run_pennylane

        result = run_pennylane(
            DEFAULT_EDGES,
            DEFAULT_N_NODES,
            p=args.p,
            steps=args.steps,
            restarts=args.restarts,
            shots=args.shots,
            seed=args.seed,
        )
    else:
        result = optimize_qaoa(
            p=args.p,
            steps=args.steps,
            restarts=args.restarts,
            seed=args.seed,
            n_qubits=DEFAULT_N_NODES,
            edges=DEFAULT_EDGES,
        )
        distribution = probability_distribution(
            result["gammas"], result["betas"], DEFAULT_N_NODES, DEFAULT_EDGES
        )
        result["counts"] = sample_counts(distribution, args.shots, args.seed)

    summary = build_summary(result, exact, DEFAULT_EDGES, args.shots)
    summary["random_partition_expected_cut"] = random_cut_expectation(DEFAULT_EDGES)
    json_path, csv_path = save_outputs(summary, args.output)

    print("\n=== QAOA MAX-CUT PROJECT ===")
    print(f"Backend: {summary['backend']}")
    print(f"Graph: {summary['n_qubits']} nodes, {summary['n_edges']} edges")
    print(f"QAOA depth p: {summary['qaoa_depth_p']}")
    print(f"QAOA expected cut: {summary['qaoa_expected_cut_exact_during_optimization']:.4f}")
    print(f"Exact classical optimum: {summary['classical_exact_optimum']:.4f}")
    print(f"Expected-cut approximation ratio: {summary['approximation_ratio_expected_cut']:.4f}")
    print(f"Optimal bitstrings: {', '.join(summary['optimal_bitstrings'])}")
    print(f"Optimal samples: {summary['optimal_sample_count']} / {summary['shots']}")
    print("\nTop measured outcomes:")
    for item in summary["top_measurement_outcomes"][:5]:
        print(
            f"  {item['bitstring']}  count={item['count']:>5}  "
            f"cut={item['cut_value']:.1f}  {item['partition']}"
        )
    print("\nSaved:")
    print(f"  {json_path}")
    print(f"  {csv_path}")
    print("\nNote: simulator demonstration only; no real-hardware advantage is claimed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
