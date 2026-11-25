# QAOA for Max-Cut - Project Overview

## Objective

Explore a small combinatorial optimization problem using the Quantum Approximate Optimization Algorithm (QAOA). The task is to divide four graph nodes into two groups while maximizing the number of edges crossing between the groups.

## Approach

Each graph node is represented by one qubit. The Max-Cut objective is translated into a cost Hamiltonian, and the circuit alternates cost operations with a mixer Hamiltonian. The QAOA angles, gamma and beta, are updated by a classical optimizer. Sampling the circuit produces bitstrings, which are scored using the original graph objective.

## Validation strategy

An exact classical search evaluates all 16 possible assignments and establishes the optimum cut value of 4. A separate NumPy state-vector simulator provides an inspectable reference implementation. The PennyLane implementation is included as a framework-based backend.

## Verified reference result

The saved NumPy run used QAOA depth `p=1`, 10 optimizer restarts, 250 COBYLA iterations per restart, 5,000 measurement shots and random seed 7. The expected cut was 3.2371, corresponding to an expected-value approximation ratio of 0.8093 against the exact optimum of 4. The optimal bitstrings `0101` and `1010` appeared in 1,706 of the 5,000 samples (34.12%).

These results are from a tiny simulator experiment. They do not establish scalability or quantum advantage.

## Implementation and next steps

The repository includes a command-line interface, separate problem and backend modules, JSON/CSV reporting, automated tests and a GitHub Actions workflow. Useful next experiments include increasing QAOA depth, testing weighted graphs, comparing optimizers, introducing finite-shot optimization and noise, and eventually benchmarking a compatible QPU against classical heuristics.

## Execution status

The NumPy reference backend was executed and the automated test suite passed in the validated project environment. The PennyLane backend has not yet been executed in that environment. No physical QPU was accessed.
