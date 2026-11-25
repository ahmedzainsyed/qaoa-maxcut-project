"""Shared reporting and output-file helpers."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .problem import cut_value, partition_label


def build_summary(result: dict, exact: dict, edges: tuple, shots: int) -> dict:
    counts = result["counts"]
    total = sum(counts.values())
    scored = [
        {"bitstring": bits, "count": count, "probability": count / total,
         "cut_value": cut_value(bits, edges), "partition": partition_label(bits)}
        for bits, count in counts.items()
    ]
    scored.sort(key=lambda item: (-item["cut_value"], -item["count"], item["bitstring"]))
    optimal = exact["optimal_cut_value"]
    optimal_shots = sum(item["count"] for item in scored if item["cut_value"] == optimal)
    return {
        "project": "QAOA for Max-Cut",
        "backend": result.get("framework", "NumPy reference state-vector simulator"),
        "n_qubits": exact["n_nodes"],
        "n_edges": len(edges),
        "qaoa_depth_p": result["p"],
        "optimizer_steps_per_restart": result["steps_per_restart"],
        "restarts": result["restarts"],
        "shots": total,
        "qaoa_expected_cut_exact_during_optimization": result["expected_cut"],
        "classical_exact_optimum": optimal,
        "approximation_ratio_expected_cut": result["expected_cut"] / optimal if optimal else None,
        "optimal_bitstrings": exact["optimal_bitstrings"],
        "optimal_sample_count": optimal_shots,
        "optimal_sample_probability": optimal_shots / total if total else 0.0,
        "top_measurement_outcomes": scored[:10],
        "important_note": (
            "This is a small simulator experiment. Exhaustive search is used only "
            "to verify the tiny instance; no quantum speedup or hardware advantage is claimed."
        ),
    }


def save_outputs(summary: dict, output_dir: str | Path) -> tuple[Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "run_summary.json"
    csv_path = directory / "measurement_results.csv"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fields = ["bitstring", "count", "probability", "cut_value", "partition"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary["top_measurement_outcomes"])
    return json_path, csv_path
