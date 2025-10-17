# Fat Tree Topology Simulator

## Overview

`simulador_fat_tree.py` implements a multi-commodity flow optimization simulator for a k-ary fat tree data center network topology. The simulator creates a fat tree with k=8, generates 100 random traffic flows, and optimizes the routing to minimize network congestion.

## Network Topology

### Fat Tree Structure (k=8)
- **128 hosts** organized in a 3-level Clos network
- **32 edge switches** (bottom layer, connected to hosts)
- **32 aggregation switches** (middle layer)
- **16 core switches** (top layer, provides full bisection bandwidth)
- **768 bidirectional links** total

### Topology Characteristics
- **k pods**, each containing:
  - k/2 edge switches
  - k/2 aggregation switches
  - Each edge switch connects to k/2 hosts
- **Equal-Cost Multi-Path (ECMP)**: Multiple paths between hosts through different core switches
- **Uniform link capacity**: All links have capacity = 100 units

### Node Numbering Scheme
- Hosts: 0 to 127
- Edge switches: 128 to 191
- Aggregation switches: 192 to 255
- Core switches: 256 to 271

## Traffic Pattern

### Flow Generation
- **100 random commodities** (source-destination pairs)
- **Requirement per flow**: 50 units (50% of link capacity)
- **Random seed**: 42 (for reproducibility)
- Flows are randomly distributed among the 128 hosts

### Path Selection
- Each commodity has up to **3 candidate paths**
- Paths found using BFS-based k-shortest path algorithm
- Paths utilize ECMP diversity through different core switches

## Optimization Process

The simulator uses the convex optimization algorithm from `funciones.py`:

1. **Initialization**: Traffic distributed uniformly across all 3 paths per commodity
2. **Iterative optimization** (200 iterations):
   - Calculate flow on each link (sum of all paths using that link)
   - Compute path costs using convex cost function: f'(capacity, flow)
   - Identify shortest (minimum cost) path for each commodity
   - Update traffic on non-shortest paths using gradient projection
   - Assign residual traffic to shortest path to maintain flow conservation
3. **Convergence**: Iterates until traffic distribution stabilizes

### Cost Function
- Uses convex function: `capacity / (capacity - flow)^2`
- Heavily penalizes flows when utilization > 99% of capacity
- Drives traffic toward less congested paths

## Key Metrics Reported

### During Execution
- Topology generation time
- Path finding time (for 100 commodities × 3 paths each)
- Number of paths found per commodity
- Per-iteration flow and cost updates

### Final Analysis
1. **Top 10 most utilized links** with utilization percentages
2. **Path cost statistics**: min, max, average costs
3. **Flow conservation verification**: Ensures each commodity's requirement is satisfied
4. **Total simulation time**

## Performance Characteristics

### Computational Complexity
- Path finding: Most expensive operation (~25 seconds for 100 flows)
  - BFS/DFS explores large state space due to mesh topology
  - 768 links create many possible paths
- Optimization: 200 iterations over 100 commodities × ~300 total paths

### Scalability
- Handles 100 commodities with ~292 paths efficiently
- Memory usage scales with: O(commodities × paths × links_per_path)
- Can stress-test data center network designs

## Usage

```bash
python3 simulador_fat_tree.py
```

### Expected Output
1. Network topology statistics
2. Flow generation summary
3. Real-time iteration progress (iterations 0-199)
4. Final utilization analysis
5. Flow conservation verification

### Typical Results
- **High utilization** on edge-to-host links (70-90%)
- **Moderate utilization** on aggregation links (40-60%)
- **Low utilization** on core links due to high capacity and path diversity
- **Full flow conservation**: All commodities satisfy their 50-unit requirements

## Configuration Parameters

Modify these in `main()` to experiment:

```python
k = 8                      # Fat tree size (must be even)
link_capacity = 100.0      # Capacity of all links
num_flows = 100            # Number of commodities
flow_requirement = 50.0    # Traffic demand per commodity
num_paths_per_flow = 3     # Candidate paths per commodity
random_seed = 42           # For reproducible flow placement
```

## Dependencies

- `modelos.py`: Enlace, Commodity, Path classes
- `funciones.py`: Optimization algorithm (funcion_principal)
- `fat_tree_topology.py`:
  - `generar_fat_tree()`: Topology generation
  - `encontrar_k_paths_mas_cortos()`: Path finding
  - `generar_pares_aleatorios()`: Random flow generation

## Use Cases

1. **Data center network analysis**: Evaluate fat tree performance under various traffic patterns
2. **Load balancing research**: Study ECMP and traffic engineering
3. **Capacity planning**: Determine link capacities needed for target traffic loads
4. **Algorithm validation**: Test multi-commodity flow optimization algorithms
5. **Teaching**: Demonstrate data center network architectures and optimization

## Limitations

- Fixed k=8 topology (128 hosts)
- Uniform link capacities (no heterogeneous networks)
- Random traffic matrix (not based on real data center workloads)
- Path finding can be slow for very large k values due to exponential path growth
- 200 iterations fixed (no dynamic convergence detection)
