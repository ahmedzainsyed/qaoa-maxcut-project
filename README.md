# QAOA for Max-Cut

An end-to-end exploration of the **Quantum Approximate Optimization Algorithm (QAOA)** applied to a small **Max-Cut** problem. The repository contains a PennyLane circuit implementation, an independent NumPy state-vector reference simulator, an exact classical baseline, automated tests, and a reproducible reference experiment.

The project focuses on translating a combinatorial optimization problem into a quantum cost Hamiltonian, implementing a hybrid quantum-classical workflow, measuring candidate solutions, and validating results against a classical reference.

> **Verification note:** The saved experiment was generated with the NumPy reference simulator. The PennyLane backend is included as runnable source code but has not yet been executed in the build environment. No physical quantum processing unit (QPU) was accessed. No quantum speedup or advantage is claimed.

---

## 1. Project overview

**Problem:** Divide four connected graph nodes into two groups so that the total weight of edges crossing between the groups is as large as possible.

**Quantum approach:** Represent each node with one qubit and use QAOA cost and mixer layers to prepare a distribution over candidate partitions. A classical optimizer adjusts the QAOA angles.

**Evaluation:** Compare the measured solutions with an exact classical search over all 16 possible bitstrings. This exact search is feasible only because the example is deliberately small.

| Item | Value |
|---|---:|
| Graph nodes / qubits | 4 |
| Graph edges | 5 |
| Possible bitstrings | 16 |
| Exact Max-Cut optimum | 4 |
| QAOA depth in saved reference run | p = 1 |
| Measurement shots in saved reference run | 5,000 |

## 2. Repository structure

```text
qaoa-maxcut-project/
├── .github/
│   └── workflows/
│       └── tests.yml                 # GitHub Actions test workflow
├── docs/
│   ├── PROJECT_GUIDE.md              # Detailed project walkthrough
│   ├── PROJECT_OVERVIEW.md           # Concise technical overview
│   ├── QAOA_MaxCut_Project_Guide.pdf # PDF version of the walkthrough
│   ├── maxcut_graph.png              # Graph/problem illustration
│   └── measurement_counts.png        # Sample output visualization
├── results/
│   ├── reference_numpy_run_summary.json
│   └── reference_numpy_measurements.csv
├── src/
│   └── qaoa_maxcut/
│       ├── __init__.py
│       ├── problem.py                 # Graph, objective, QUBO/Ising and exact baseline
│       ├── reference_simulator.py     # Transparent NumPy state-vector simulator
│       ├── optimize_reference.py      # Classical parameter search for NumPy backend
│       ├── pennylane_backend.py       # QAOA circuit and optimizer using PennyLane
│       └── reporting.py               # JSON/CSV result generation
├── tests/
│   ├── test_problem.py
│   └── test_reference_simulator.py
├── .gitignore
├── LICENSE
├── NOTICE.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── run_project.py                     # Main command-line entry point
```

## 3. Understand the problem

The graph has five connections:

```text
0 -- 1
|  / |
| /  |
3 -- 2
```

Each node is assigned to one of two groups:

- `0` means Group A.
- `1` means Group B.

An edge contributes its weight if its endpoints are in different groups. For example, `0101` assigns Nodes 0 and 2 to A, and Nodes 1 and 3 to B. Four edges cross the groups, so the cut value is 4. The exact optimum is 4; `1010` is the same partition with the group labels swapped.

This is a small teaching graph, not a validated real-world energy-control or energy-savings model.

## 4. Mathematical formulation

For binary node variables \(x_i\in\{0,1\}\), the contribution of edge \((i,j)\) is:

\[
C_{ij}=x_i(1-x_j)+x_j(1-x_i)
\]

The Max-Cut objective is:

\[
C(x)=\sum_{(i,j)\in E}w_{ij}C_{ij},\qquad \max_x C(x)
\]

Map binary variables to spins using \(s_i=1-2x_i\). Then:

\[
C_{ij}=\frac{1-s_is_j}{2}
\]

Replacing spin values with Pauli-Z operators gives the cost Hamiltonian:

\[
H_C=\sum_{(i,j)\in E}w_{ij}\frac{I-Z_iZ_j}{2}
\]

The standard QAOA mixer Hamiltonian is:

\[
H_M=\sum_i X_i
\]

The parameterized operations are:

\[
U_C(\gamma)=e^{-i\gamma H_C},\qquad U_M(\beta)=e^{-i\beta H_M}
\]

The circuit starts in \(|+\rangle^{\otimes n}\), applies cost and mixer layers for depth \(p\), and measures the expected value of \(H_C\). A classical optimizer updates \(\gamma\) and \(\beta\) to maximize that expected cut. In code, the objective is written as **negative expected cut** because the optimizers minimize.

## 5. End-to-end workflow

1. **Frame the problem:** define nodes, edges, weights and the objective.
2. **Build a classical verifier:** score a partition and enumerate all 16 assignments to find the exact optimum.
3. **Encode the objective:** express Max-Cut as a QUBO/Ising cost and a quantum cost Hamiltonian.
4. **Prepare the circuit:** apply Hadamard gates to create an equal superposition.
5. **Apply QAOA layers:** apply edge-based cost interactions followed by RX mixer rotations.
6. **Optimize parameters:** use a classical optimizer to update gamma and beta.
7. **Measure:** sample the optimized circuit for a configured number of shots.
8. **Evaluate:** score bitstrings, compare with the exact classical optimum, and export JSON/CSV results.
9. **Assess feasibility:** consider circuit depth, shots, noise, compilation overhead and total runtime before real-hardware experiments.

## 6. Technology stack

- **Python 3.10-3.12** - application and experiment code.
- **PennyLane** - quantum circuit construction, expectation values, differentiation and `default.qubit` simulation.
- **NumPy** - transparent reference state-vector simulator and numerical operations.
- **SciPy** - derivative-free optimization for the reference backend.
- **pytest** - automated tests.
- **GitHub Actions** - automated tests on pushes and pull requests.

## 7. Setup

Use Python 3.11 or 3.12 (Python 3.10 is also supported by the package metadata).

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If you only need runtime dependencies, use `python -m pip install -e .`.

## 8. Run the project

Run the PennyLane backend:

```bash
python run_project.py --backend pennylane --p 1 --steps 150 --restarts 4 --shots 5000 --seed 7
```

Run the independent NumPy reference backend:

```bash
python run_project.py --backend numpy --p 1 --steps 250 --restarts 10 --shots 5000 --seed 7
```

The command writes `outputs/run_summary.json` and `outputs/measurement_results.csv`. These are generated files and are ignored by Git; the checked-in `results/` folder preserves the reference run used in the documentation.

Useful options:

| Option | Meaning | Default |
|---|---|---:|
| `--backend` | `pennylane` or `numpy` | `pennylane` |
| `--p` | QAOA layer depth | 1 |
| `--steps` | Optimizer steps per restart | 150 |
| `--restarts` | Independent parameter initializations | 4 |
| `--shots` | Number of measurements | 5000 |
| `--seed` | Random seed | 7 |
| `--output` | Output directory | `outputs/` |

## 9. Run tests

```bash
python -m pytest
```

The test suite checks:

- the known partition `0101` has cut value 4;
- QUBO energy equals negative cut value;
- binary and Ising formulations agree for every assignment;
- exact search finds optimum 4 among 16 assignments;
- the `MaxCutProblem` class evaluates the graph correctly;
- the reference state vector remains normalized;
- zero QAOA layers produce a uniform distribution and random-partition expected cut;
- finite-shot sampling returns the requested number of shots.

## 10. Reference experiment and interpretation

The saved reference run used the NumPy state-vector simulator, QAOA depth `p=1`, 10 optimizer restarts, 250 COBYLA iterations per restart, and 5,000 measurement shots.

| Metric | Saved reference result |
|---|---:|
| QAOA expected cut | 3.2371 |
| Exact classical optimum | 4.0000 |
| Expected-value approximation ratio | 0.8093 |
| Optimal measured outcomes | 1,706 / 5,000 |
| Optimal measured-outcome probability | 34.12% |
| Optimal bitstrings | `0101`, `1010` |

The approximation ratio here is the expected cut divided by the exact optimum. It is not the probability of measuring the optimum. The optimal-outcome probability is reported separately.

**Interpretation:** The reference simulator demonstrates that the circuit and objective are connected correctly and that QAOA can put substantial probability on optimal partitions for this small instance. Since the graph has only four nodes, exhaustive classical search is trivial. These results do not demonstrate quantum advantage.

## 11. Limitations and next experiments

This is a compact learning and research project, not a production optimization platform.

- Four nodes are too few to establish scalability.
- State-vector simulation requires memory that grows exponentially with qubit count.
- Results depend on optimizer initialization, depth, parameter settings and finite shots.
- Real devices introduce gate errors, readout errors, connectivity restrictions and queue/runtime costs.
- A fair hardware study must include transpilation, repetitions, calibration context, wall-clock time and a competitive classical baseline.
- For larger Max-Cut instances, compare with classical heuristics or approximation algorithms rather than relying on exhaustive search.

Recommended next experiments:

1. Increase QAOA depth from `p=1` to `p=2` and compare expected cut and circuit depth.
2. Change edge weights and test a weighted graph.
3. Compare multiple classical optimizers and initializations.
4. Add finite-shot estimation during optimization and compare with exact expectation values.
5. Run on an available cloud QPU only after selecting a compatible device, compiling to native gates and recording noise and runtime metadata.

## 12. Current implementation status

- The NumPy reference backend was executed and its results are stored in `results/`.
- Eight automated tests passed in the validated project environment.
- The PennyLane backend is present in the source tree but has not yet been executed in the build environment. Install the dependencies and run the documented command before treating that experiment as complete.
- No physical QPU was accessed.
- No quantum speedup, quantum advantage or commercial advantage is claimed.

For a concise technical summary, see [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md).

---

## References

- Farhi, Goldstone and Gutmann, *A Quantum Approximate Optimization Algorithm* (2014): https://arxiv.org/abs/1411.4028
- PennyLane QAOA Max-Cut demo: https://pennylane.ai/qml/demos/tutorial_qaoa_maxcut
- PennyLane documentation: https://docs.pennylane.ai/
