# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-commodity flow optimization simulator that implements a convex optimization algorithm for network traffic routing. The simulator finds optimal paths for multiple commodities (traffic demands) through a network while respecting link capacity constraints.

## Core Architecture

The codebase is organized into three main modules:

### modelos.py
Contains the fundamental data structures:
- `Enlace`: Represents network links with source, target, and capacity
- `Path`: Represents a routing path as a sequence of Enlaces, tracks traffic assigned to it
- `Commodity`: Represents a traffic demand from source to target with a requirement amount, contains multiple possible Paths

Key relationship: Each Commodity has multiple Paths, and each Path consists of multiple Enlaces. The same Enlace can be shared across different Paths and Commodities.

### funciones.py
Contains the optimization algorithm implementation:
- `f_prima()`: First derivative of the cost function (capacity/(capacity-flow)^2)
- `f_double_prima()`: Second derivative used for calculating step sizes
- `distribuir_trafico_uniforme()`: Initializes traffic uniformly across all paths for a commodity
- `calcular_flujo_por_enlace()`: Aggregates traffic across all paths to compute total flow per link
- `calcular_coste_total_por_path()`: Computes the cost of each path based on current link flows
- `seleccionar_path_minimo_coste()`: Identifies the shortest (lowest cost) path for each commodity
- `calcular_H_kp()`: Computes the Hessian approximation for step size calculation
- `calculo_del_trafico_para_la_siguiente_iteracion()`: Updates traffic assignment using gradient projection
- `funcion_principal()`: Main optimization loop that iterates until convergence

### simulador.py
The entry point that defines a specific network topology and runs the simulation. It:
1. Creates Enlaces (network links)
2. Defines Commodities with source, target, and demand requirements
3. Associates multiple candidate Paths to each Commodity
4. Calls `funcion_principal()` to run the optimization

## Algorithm Flow

The optimization follows this iterative process:

1. **Initialization (t=0)**: Distribute traffic uniformly across all paths for each commodity
2. **For each iteration t > 0**:
   - Calculate total flow on each link by summing traffic from all paths using that link
   - Compute cost for each path based on current link flows using f_prima()
   - Identify the minimum cost path (β) for each commodity
   - For non-minimum paths: update traffic using gradient projection with step size H_kp
   - For minimum cost path: assign residual traffic to satisfy total commodity requirement
3. **Output**: Print flow per link, cost per path, and shortest path for each commodity

The algorithm minimizes total network cost while ensuring that flow conservation holds (sum of traffic across all paths equals the commodity requirement).

## Running the Simulation

Execute the simulator:
```bash
python simulador.py
```

The simulator runs for 200 iterations and prints detailed output for each iteration showing:
- Flow on each link
- Cost of each path
- Shortest path for each commodity
- Traffic updates with intermediate calculations (t, x_kp, H_kp, d_kp, d_kbeta)

## Key Implementation Details

- **Capacity constraint**: The cost function f_prima() uses p=0.99, meaning flows are heavily penalized when exceeding 99% of link capacity
- **Gradient projection**: Traffic updates use `max(0.0, ...)` to ensure non-negative flows
- **Flow conservation**: After updating non-shortest paths, the shortest path receives residual traffic to satisfy the commodity's total requirement
- **Symmetric difference**: H_kp calculation uses symmetric difference of link sets between current and best path to determine which links affect the gradient
- **Iteration tracking**: The `iteraciones` dictionary stores historical data (flujo_total, costes_path, shortest_paths) for all iterations

## Modifying the Network

To test different scenarios, edit simulador.py:
- Add/modify Enlaces to change network topology
- Create new Commodities with different source/target/requirement values
- Associate different path combinations to commodities using `commodity.add_path()`
- Adjust the number of iterations in funciones.py:117

## Dependencies

The code uses only Python standard library modules:
- `typing` for type hints
- `collections.defaultdict` for flow aggregation
