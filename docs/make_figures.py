"""Create simple explanatory figures for the project guide."""
from pathlib import Path
import json
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUTS = ROOT / "outputs"
DOCS.mkdir(exist_ok=True)

# Four-node example graph. The optimal bitstring 0101 is used to color groups.
positions = {
    0: (0.0, 1.0),
    1: (1.3, 1.0),
    2: (1.3, 0.0),
    3: (0.0, 0.0),
}
edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
assignment = {0: 0, 1: 1, 2: 0, 3: 1}
fig, ax = plt.subplots(figsize=(7.0, 4.6))
for i, j in edges:
    x1, y1 = positions[i]
    x2, y2 = positions[j]
    cut = assignment[i] != assignment[j]
    ax.plot([x1, x2], [y1, y2], linewidth=2.5 if cut else 1.6,
            linestyle="-" if cut else "--", alpha=0.85 if cut else 0.5)
for node, (x, y) in positions.items():
    ax.scatter([x], [y], s=1400, zorder=3, facecolors="white", edgecolors="black", linewidths=1.5)
    ax.text(x, y, f"Node {node}\nGroup {'B' if assignment[node] else 'A'}",
            ha="center", va="center", fontsize=10, weight="bold", zorder=4)
ax.set_title("Max-Cut example: the partition 0101 cuts 4 of 5 edges", fontsize=12, pad=16)
ax.text(0.65, -0.24, "Solid edge = crosses groups    |    Dashed edge = same group",
        ha="center", va="center", fontsize=9)
ax.set_xlim(-0.5, 1.8)
ax.set_ylim(-0.35, 1.35)
ax.axis("off")
fig.tight_layout()
fig.savefig(DOCS / "maxcut_graph.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# Top measurement outcomes from the verified NumPy run.
summary = json.loads((OUTPUTS / "run_summary.json").read_text())
rows = summary["top_measurement_outcomes"]
labels = [r["bitstring"] for r in rows]
counts = [r["count"] for r in rows]
fig, ax = plt.subplots(figsize=(8.0, 4.6))
ax.bar(labels, counts)
ax.set_title("Most frequent measurement outcomes (5,000 shots)")
ax.set_xlabel("Measured bitstring")
ax.set_ylabel("Number of shots")
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(DOCS / "measurement_counts.png", dpi=180, bbox_inches="tight")
plt.close(fig)
