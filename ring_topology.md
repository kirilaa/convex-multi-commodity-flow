# Access Network Ring Topology Simulator

## Overview

`simulador_access_network.py` implements a multi-commodity flow optimization simulator for a hierarchical access network with ring topology. The network consists of 20 access rings connected to an aggregation layer, designed to create a bottleneck at the access layer and exhaust 100% of access link capacity with 100 traffic flows.

## Network Architecture

### Hierarchical Structure

```
┌─────────────────────────────────────────┐
│     Aggregation Layer (30 nodes)        │
│   Full mesh, capacity = 200 units       │
└──────────────┬──────────────────────────┘
               │ Uplink
               │ capacity = 100 units
               │
┌──────────────┴──────────────────────────┐
│        20 Access Rings                   │
│  Each ring: 10 nodes, capacity = 50     │
│  Bidirectional ring topology             │
└──────────────────────────────────────────┘
```

### Access Layer (Bottleneck)
- **20 access rings**, each with **10 nodes** (200 access nodes total)
- **Bidirectional ring topology**: Node i connects to node (i+1) % 10 in both directions
- **Link capacity**: 50 units (intentionally low to create bottleneck)
- **400 bidirectional links** in access rings

### Aggregation Layer
- **30 aggregation nodes**
- **Full mesh topology**: Every aggregation node connects to every other
- **Link capacity**: 200 units (high capacity backbone)
- **870 bidirectional links** (30 choose 2 × 2)

### Uplink Connections
- Each access ring's **gateway node** (node 0 of each ring) connects to **2 aggregation nodes**
- **80 bidirectional uplink connections** (20 rings × 2 connections × 2 directions)
- **Link capacity**: 100 units (medium capacity)

### Node Numbering
- **Access nodes**: 0 to 199 (ring 0: nodes 0-9, ring 1: nodes 10-19, ..., ring 19: nodes 190-199)
- **Aggregation nodes**: 200 to 229

## Traffic Pattern

### 100 Commodities Designed to Exhaust Access Layer

#### Capacity Calculation
- Total access links: 20 rings × 10 links/ring = 200 links
- Total access capacity: 200 links × 50 units/link = 10,000 units
- **Requirement per commodity**: 10,000 / 100 = **100 units**
- **Total aggregate demand**: 100 commodities × 100 units = 10,000 units = **100% of access capacity**

#### Traffic Mix
- **50% intra-ring traffic** (50 commodities):
  - Source and destination in the same access ring
  - Traffic stays within the ring, stressing ring links
- **50% inter-ring traffic** (50 commodities):
  - Source and destination in different access rings
  - Traffic must traverse uplink → aggregation → uplink
  - Stresses both access and uplink layers

#### Flow Generation
- Random seed: 42 (reproducibility)
- Source/destination pairs selected strategically to balance load
- Avoids trivial same-node commodities

### Path Diversity
- Each commodity has up to **3 candidate paths**
- **Intra-ring paths**: Clockwise, counter-clockwise, possibly through gateway
- **Inter-ring paths**: Various routes through aggregation mesh
- **Max path length**: 10 hops (prevents excessively long paths)

## Optimization Process

Uses the same convex optimization from `funciones.py`:

1. **Initialization**: Uniform traffic distribution across paths
2. **200 iterations** of gradient projection:
   - Aggregate flow per link
   - Compute path costs: f'(c, x) = c/(c-x)²
   - Select minimum cost path per commodity
   - Update non-minimum paths: projection step
   - Assign residual to minimum path (flow conservation)
3. **Convergence**: Traffic shifts to less congested paths

### Bottleneck Behavior
- Access links (capacity=50) saturate first
- Algorithm balances load across ring links
- Some commodities may not achieve full 100-unit requirement if access is over-subscribed

## Key Metrics Reported

### Network Statistics
- Total nodes, links by layer
- Access/uplink/aggregation link counts
- Intra-ring vs inter-ring commodity distribution

### Final Analysis by Layer

#### 1. Access Layer (Bottleneck)
- Number of access links
- **Average utilization** (target: ~100%)
- **Maximum utilization** (should approach 100%)
- Minimum utilization
- Top 10 most congested access links

#### 2. Uplink Layer
- Number of uplink connections
- Average/maximum utilization
- Shows if inter-ring traffic is balanced

#### 3. Aggregation Layer
- Active links (some may be unused due to topology)
- Average/maximum utilization (typically low due to high capacity)

### Flow Conservation
- Verifies each commodity's traffic sums to its requirement
- Reports violations (if any)
- Essential for validating optimization correctness

## Performance Characteristics

### Computational Profile
- **Topology generation**: Very fast (<0.1s)
  - Simple ring structures
  - Full mesh is straightforward
- **Path finding**: Moderate (~10-30s for 100 commodities)
  - Full mesh aggregation creates many paths
  - DFS explores large state space
- **Optimization**: Similar to fat tree (~200 iterations)

### Scalability
- 100 commodities × ~3 paths = 300 path objects
- ~1,350 total links (400 access + 80 uplink + 870 aggregation)
- Memory and time scale linearly with commodities and links

## Usage

```bash
python3 simulador_access_network.py
```

### Expected Output
1. Network configuration parameters
2. Topology generation summary
3. Commodity generation statistics
4. Path finding progress (20/40/60/80/100)
5. Optimization iterations (0-199)
6. Layer-by-layer utilization analysis
7. Flow conservation verification

### Typical Results
- **Access layer**: 80-100% average utilization (bottleneck working as designed)
- **Uplink layer**: 40-70% utilization (inter-ring traffic)
- **Aggregation layer**: 10-30% utilization (over-provisioned)
- **Flow conservation**: Most commodities satisfied, some violations possible if over-subscribed

## Configuration Parameters

Modify these in `main()` to experiment:

```python
num_access_rings = 20         # Number of access rings
nodes_per_ring = 10           # Nodes per access ring
num_agg_nodes = 30            # Aggregation layer nodes

access_capacity = 50.0        # Access link capacity (bottleneck)
uplink_capacity = 100.0       # Uplink capacity
agg_capacity = 200.0          # Aggregation capacity

num_commodities = 100         # Number of flows
intra_ring_ratio = 0.5        # 50% intra-ring, 50% inter-ring
```

### Experiment Ideas
1. **Increase access capacity** to 100: Bottleneck shifts to uplink
2. **Change intra_ring_ratio** to 0.8: More local traffic, less aggregation load
3. **Reduce num_agg_nodes** to 10: Aggregation becomes bottleneck
4. **Increase num_commodities** to 200: Over-subscription, observe flow violations

## Dependencies

- `modelos.py`: Enlace, Commodity, Path classes
- `funciones.py`: Optimization algorithm
- `ring_topology.py`:
  - `generar_anillo_simple()`: Creates bidirectional ring
  - `generar_red_acceso_agregacion()`: Builds full hierarchy
  - `encontrar_k_paths_bfs()`: BFS-based path finding with max length
  - `generar_commodities_estrategicos()`: Strategic flow placement

## Use Cases

1. **Access network design**: Evaluate ring topology performance
2. **Capacity planning**: Determine where to upgrade (access vs uplink vs aggregation)
3. **Over-subscription analysis**: Test network under high load
4. **Traffic engineering**: Study intra-ring vs inter-ring traffic patterns
5. **Bottleneck identification**: Validate that access layer is the constraint
6. **Cost optimization**: Minimize total network cost subject to performance constraints

## Key Differences from Fat Tree Simulator

| Aspect | Fat Tree | Ring Access Network |
|--------|----------|---------------------|
| **Topology** | 3-level Clos, highly redundant | 2-level hierarchical with rings |
| **Bottleneck** | Typically none (full bisection bandwidth) | Intentional at access layer |
| **Link capacity** | Uniform (100) | Tiered (50/100/200) |
| **Path diversity** | High (ECMP through cores) | Moderate (ring directions + agg mesh) |
| **Traffic goal** | Random, 50% capacity per flow | Exhaust 100% of access capacity |
| **Use case** | Data center | Access/metro network |

## Limitations

- Full mesh aggregation may be unrealistic (consider ring or partial mesh)
- Path finding slow due to mesh (could optimize with pruning)
- Fixed 200 iterations (no convergence detection)
- Uniform commodity requirements (real networks have heterogeneous demands)
- No link failures or redundancy testing
- Gateway node per ring is single point of failure (could add redundancy)
