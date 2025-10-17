# Dual-Gateway Ring Topology Implementation

## Overview

This document describes the implementation of **dual-gateway rings** in the access network simulator. This enhancement provides redundancy, load balancing, and increased throughput for inter-ring traffic by having **two gateway nodes per ring** instead of one.

## Motivation

### Problems with Single-Gateway Design
1. **Single point of failure**: If gateway fails, entire ring is isolated
2. **Bottleneck**: All inter-ring traffic must pass through one node
3. **Limited capacity**: Gateway uplinks become saturated under high load
4. **No redundancy**: No failover path if gateway-to-aggregation link fails

### Benefits of Dual-Gateway Design
1. **Fault tolerance**: Ring remains connected if one gateway fails
2. **Load balancing**: Traffic distributes across two gateways
3. **2× uplink capacity**: Double the bandwidth for inter-ring traffic
4. **Path diversity**: More routing options for optimization algorithm
5. **Graceful degradation**: Performance drops 50% (not 100%) on failure

## Architecture

### Gateway Placement

```
Ring with 10 nodes:

         GW1 (node 0)
          ↑ ↑
          | |  (to aggregation layer)
          | |
    9 ← 0 ← 1 ← 2 ← 3
    ↓           ↓
    8           4
    ↓           ↓
    7 → 6 → 5 → GW2 (node 5)
          ↓ ↓
          | |  (to aggregation layer)
          | |
```

- **Gateway 1**: Node 0 (first node of ring)
- **Gateway 2**: Node `nodes_per_ring // 2` (midpoint of ring)

This placement ensures:
- Symmetric positioning in the ring
- Maximum distance between gateways (fault isolation)
- Balanced access from all ring nodes

### Uplink Connectivity

Each gateway connects to **different aggregation nodes** to maximize diversity:

```
Ring 0:
  Gateway 1 (node 0) → Agg nodes [200, 201]
  Gateway 2 (node 5) → Agg nodes [202, 203]

Ring 1:
  Gateway 1 (node 10) → Agg nodes [204, 205]
  Gateway 2 (node 15) → Agg nodes [206, 207]

... (pattern continues)
```

**Connection formula**:
- Gateway 1: `agg_nodes[(ring_id * 4 + 0..1) % num_agg]`
- Gateway 2: `agg_nodes[(ring_id * 4 + 2..3) % num_agg]`

Each gateway connects to `connections_per_gateway` aggregation nodes (default: 2).

## Implementation Details

### 1. Topology Generation (`ring_topology.py`)

#### Modified Function: `generar_red_acceso_agregacion()`

**Changes**:
- Calculate two gateway nodes per ring instead of one
- Create uplink connections for both gateways
- Ensure gateways connect to different aggregation nodes
- Store gateway information in `info['gateway_info']`

**Code structure**:
```python
for ring_id in range(num_access_rings):
    # Define gateways
    gateway_node_1 = ring_id * nodes_per_ring
    gateway_node_2 = ring_id * nodes_per_ring + (nodes_per_ring // 2)

    # Connect Gateway 1 to aggregation nodes
    for i in range(connections_per_ring):
        agg_idx = (ring_id * connections_per_ring * 2 + i) % num_agg_nodes
        # Create bidirectional links...

    # Connect Gateway 2 to DIFFERENT aggregation nodes
    for i in range(connections_per_ring):
        agg_idx = (ring_id * connections_per_ring * 2 + connections_per_ring + i) % num_agg_nodes
        # Create bidirectional links...
```

**New info fields**:
```python
info['gateway_info'] = [
    {
        'ring_id': 0,
        'gateway_1': 0,
        'gateway_2': 5,
        'gw1_agg_nodes': [200, 201],
        'gw2_agg_nodes': [202, 203]
    },
    # ... for each ring
]
info['connections_per_gateway'] = 2
```

### 2. Path Finding (No Changes Required)

The existing `encontrar_k_paths_bfs()` function **automatically discovers** paths through both gateways. No modifications needed because:
- The graph includes all gateway uplinks
- BFS/DFS explores all available paths
- K-shortest paths naturally includes routes through both gateways

**Path diversity improvement**:
- **Before (1 gateway)**: ~2-3 paths per inter-ring flow
- **After (2 gateways)**: ~4-6 paths per inter-ring flow

### 3. Simulator Analysis (`simulador_access_network.py`)

#### New Gateway Analysis Section

**Metrics reported**:
1. **Per-gateway utilization**: Traffic through each gateway node
2. **Load balance ratio**: GW1_util / GW2_util (ideal: ~1.0)
3. **Balanced rings**: Count rings with ratio between 0.8-1.25
4. **Top 5 most unbalanced rings**: Identify hotspots

**Output format**:
```
--- ANÁLISIS DE GATEWAYS (Dual-Gateway) ---
Total anillos con dual-gateway: 20
Utilización promedio Gateway 1: 62.3%
Utilización promedio Gateway 2: 58.7%
Balance promedio (GW1/GW2): 1.06
Anillos con carga balanceada (ratio 0.8-1.25): 18/20

Top 5 anillos con mayor desbalance de carga:
  1. Ring 7:
     GW1 (nodo 70): 185.30/200.00 (92.7%)
     GW2 (nodo 75): 134.20/200.00 (67.1%)
     Balance ratio: 1.38
  ...
```

## Capacity Analysis

### Link Counts

| Layer | Single-Gateway | Dual-Gateway | Change |
|-------|----------------|--------------|--------|
| Access ring links | 400 | 400 | No change |
| Uplink connections | 80 | **160** | **+100%** |
| Aggregation mesh | 870 | 870 | No change |
| **Total links** | **1,350** | **1,430** | **+5.9%** |

### Uplink Capacity

**Configuration**:
- 20 rings
- 2 gateways per ring
- 2 aggregation connections per gateway
- 100 units capacity per link

**Total uplink capacity**:
- Single-gateway: 20 × 1 × 2 × 100 = **4,000 units**
- Dual-gateway: 20 × 2 × 2 × 100 = **8,000 units**
- **Increase: +100%**

**Traffic demand** (50 inter-ring commodities × 100 requirement):
- Total inter-ring demand: **5,000 units**
- Single-gateway utilization: 5,000 / 4,000 = **125% (oversubscribed!)**
- Dual-gateway utilization: 5,000 / 8,000 = **62.5% (sufficient)**

### Performance Implications

With 100 commodities exhausting access layer:
- **Access layer**: Still bottleneck at ~100% (by design)
- **Uplink layer**: Reduced from 125% to 62.5% (no longer bottleneck)
- **Aggregation layer**: ~15-30% utilization (over-provisioned)

**Result**: Dual-gateway removes uplink bottleneck, allowing access layer to be the true constraint as intended.

## Expected Optimization Behavior

### Path Selection

The optimization algorithm (`funcion_principal`) will:
1. **Initial state** (t=0): Distribute traffic uniformly across all paths
2. **Early iterations**: Detect congestion on overloaded gateway
3. **Convergence**: Shift traffic to less congested gateway
4. **Equilibrium**: Balance load across both gateways (~50/50 split)

### Load Balancing

**Natural balancing occurs because**:
- Cost function penalizes congested links: `f'(c, x) = c / (c - x)²`
- Paths through congested gateway have higher cost
- Gradient projection shifts traffic to cheaper (less congested) paths
- Both gateways reach similar utilization at equilibrium

**Factors affecting balance**:
- **Commodity placement**: Random distribution may favor one gateway
- **Ring topology**: Some nodes closer to one gateway
- **Aggregation connectivity**: Gateway connected to less-loaded agg nodes preferred
- **Path diversity**: More paths through one gateway can create imbalance

## Fault Tolerance

### Gateway Failure Simulation

**Scenario**: Gateway 1 of Ring 5 fails

**Steps to simulate**:
1. Remove gateway 1 uplinks from topology
2. Re-run path finding (only finds paths through gateway 2)
3. Run optimization with reduced topology

**Expected results**:
- Flow conservation maintained (all commodities satisfied)
- Gateway 2 utilization increases to ~100%
- Some access ring links may reach saturation
- Overall throughput: ~80-90% of normal (not 50%, due to access bottleneck)

### Comparison

| Failure | Single-Gateway | Dual-Gateway |
|---------|----------------|--------------|
| Gateway node fails | **Ring isolated** | Traffic reroutes to other gateway |
| Uplink fails | **Inter-ring traffic drops 50%** | Traffic uses other gateway links |
| Aggregation node fails | Ring isolated if only connection | Ring maintains connectivity via other gateway |
| **Recovery** | **Requires manual intervention** | **Automatic rerouting** |

## Verification & Testing

### Topology Correctness

**Checks**:
1. Each ring has exactly 2 gateway nodes
2. Gateways are at positions 0 and `nodes_per_ring // 2`
3. Each gateway connects to `connections_per_gateway` agg nodes
4. No overlap in gateway-to-agg connections
5. Total uplinks = `num_rings × 2 × connections_per_gateway × 2`

**Validation**:
```python
# Count gateway nodes
gateway_nodes = set()
for gw_info in info['gateway_info']:
    gateway_nodes.add(gw_info['gateway_1'])
    gateway_nodes.add(gw_info['gateway_2'])

assert len(gateway_nodes) == num_access_rings * 2
```

### Flow Conservation

**Critical check**: Sum of path traffic equals commodity requirement

```python
for commodity in commodities:
    total_traffic = sum(path.trafico for path in commodity.paths)
    assert abs(total_traffic - commodity.requirement) < 0.01
```

If violations occur, indicates:
- Insufficient capacity (network oversubscribed)
- Optimization not converged (increase iterations)
- Path finding failed (some commodities unreachable)

### Load Balance

**Good balance indicators**:
- Average balance ratio: 0.9 - 1.1
- Most rings (>80%) within 0.8 - 1.25 ratio
- No gateway at 100% while other at <50%

**Poor balance indicators**:
- Average ratio > 1.5 or < 0.67
- Many rings with extreme ratios
- One gateway consistently overloaded

## Performance Comparison

### Metrics to Compare

| Metric | Single-Gateway | Dual-Gateway | Expected Change |
|--------|----------------|--------------|-----------------|
| Uplink utilization (avg) | ~125% | ~62% | **-50%** (capacity doubled) |
| Gateway utilization (max) | 100% | 50-70% per gateway | Better balance |
| Access utilization | ~100% | ~100% | No change (still bottleneck) |
| Paths per commodity | 2.5 | 4.2 | **+68%** (more diversity) |
| Convergence iterations | 200 | 150-180 | Faster (more options) |
| Flow violations | 5-10% | 0-2% | Fewer (sufficient capacity) |

### Computation Time

| Phase | Impact | Reason |
|-------|--------|--------|
| Topology generation | +10% | More links to create |
| Path finding | +40% | More paths to explore |
| Optimization | -20% | Better initial distribution, faster convergence |
| Analysis | +5% | Gateway statistics added |
| **Overall** | **+15-20%** | Dominated by path finding |

## Usage

### Running the Dual-Gateway Simulator

```bash
python3 simulador_access_network.py
```

### Configuration Parameters

```python
# In simulador_access_network.py:
num_access_rings = 20
nodes_per_ring = 10
connections_per_ring = 2  # Connections per gateway (not per ring!)
```

**Note**: `connections_per_ring` now means connections **per gateway**, so total uplinks = `rings × 2 gateways × connections_per_ring × 2 directions`.

### Modifying for Single-Gateway (rollback)

To revert to single gateway:
1. In `ring_topology.py`, comment out gateway 2 logic
2. In `simulador_access_network.py`, update uplink count calculation
3. Remove gateway analysis section

Or use git:
```bash
git diff ring_topology.py  # Review changes
git checkout ring_topology.py  # Revert if needed
```

## Future Enhancements

### Priority 1: Adaptive Gateway Selection
Add cost penalty for routing through specific gateways:
```python
# Prefer gateway 1 for nodes 0-4, gateway 2 for nodes 5-9
def gateway_cost_penalty(node, gateway):
    if abs(node % nodes_per_ring - gateway % nodes_per_ring) > nodes_per_ring // 2:
        return 10.0  # Penalty for using far gateway
    return 0.0
```

### Priority 2: Unequal Gateway Capacities
Support asymmetric configurations:
```python
generar_red_acceso_agregacion(
    gw1_connections=2,
    gw2_connections=1,  # Backup gateway with lower capacity
    gw1_capacity=100,
    gw2_capacity=50
)
```

### Priority 3: Gateway Failure Testing
Automated fault injection:
```python
def simulate_gateway_failure(enlaces, failed_gateway_node):
    # Remove all uplinks from failed gateway
    return [e for e in enlaces if e.source != failed_gateway_node]
```

## Conclusion

The dual-gateway implementation provides:
- **High impact**: 2× uplink capacity, fault tolerance
- **Low complexity**: ~100 lines of code changed
- **Backward compatible**: Single-gateway is special case
- **Measurable improvement**: Clear metrics in output

This enhancement makes the access network more **realistic**, **resilient**, and **scalable** for studying multi-commodity flow optimization under real-world constraints.

## References

- Original ring topology: `ring_topology.py`
- Simulator with gateway analysis: `simulador_access_network.py`
- Optimization algorithm: `funciones.py` (unchanged)
- Comparison with fat tree: `simulador_fat_tree.md`
