from modelos import Enlace
from typing import List, Tuple, Dict, Set
from collections import deque
import random


def generar_anillo_simple(
    ring_id: int,
    num_nodes: int,
    node_offset: int,
    capacity: float,
    bidirectional: bool = True
) -> List[Enlace]:
    """
    Genera un anillo simple con num_nodes nodos.

    Args:
        ring_id: Identificador del anillo
        num_nodes: Número de nodos en el anillo
        node_offset: Offset para la numeración de nodos (primer nodo será node_offset)
        capacity: Capacidad de los enlaces
        bidirectional: Si True, crea enlaces en ambas direcciones

    Returns:
        Lista de Enlaces que forman el anillo
    """
    enlaces = []

    for i in range(num_nodes):
        source = node_offset + i
        target = node_offset + ((i + 1) % num_nodes)

        # Enlace en dirección clockwise
        enlaces.append(Enlace(source, target, capacity))

        # Enlace en dirección counter-clockwise (si bidireccional)
        if bidirectional:
            enlaces.append(Enlace(target, source, capacity))

    return enlaces


def generar_red_acceso_agregacion(
    num_access_rings: int,
    nodes_per_ring: int,
    num_agg_nodes: int,
    access_capacity: float,
    uplink_capacity: float,
    agg_capacity: float,
    connections_per_ring: int = 2
) -> Tuple[List[Enlace], Dict]:
    """
    Genera una red de acceso jerárquica con anillos de acceso y capa de agregación.

    Args:
        num_access_rings: Número de anillos de acceso
        nodes_per_ring: Número de nodos por anillo de acceso
        num_agg_nodes: Número de nodos de agregación
        access_capacity: Capacidad de enlaces dentro de anillos de acceso
        uplink_capacity: Capacidad de enlaces access→aggregation
        agg_capacity: Capacidad de enlaces en la capa de agregación
        connections_per_ring: Cuántos nodos de agregación conecta cada anillo

    Returns:
        Tuple de (lista de Enlaces, diccionario con info de la red)
    """
    enlaces = []

    # Numeración de nodos
    # Access nodes: 0 to (num_access_rings * nodes_per_ring - 1)
    # Aggregation nodes: start from (num_access_rings * nodes_per_ring)

    total_access_nodes = num_access_rings * nodes_per_ring
    agg_node_offset = total_access_nodes

    access_nodes = list(range(total_access_nodes))
    agg_nodes = list(range(agg_node_offset, agg_node_offset + num_agg_nodes))

    # 1. Generar anillos de acceso
    for ring_id in range(num_access_rings):
        node_offset = ring_id * nodes_per_ring
        ring_enlaces = generar_anillo_simple(
            ring_id, nodes_per_ring, node_offset, access_capacity, bidirectional=True
        )
        enlaces.extend(ring_enlaces)

    # 2. Conectar anillos de acceso a capa de agregación
    # Estrategia: cada anillo se conecta a connections_per_ring nodos de agregación
    # Usamos un nodo "gateway" de cada anillo (el nodo 0 del anillo)

    for ring_id in range(num_access_rings):
        gateway_node = ring_id * nodes_per_ring  # Primer nodo del anillo

        # Conectar a connections_per_ring nodos de agregación
        # Distribuimos las conexiones uniformemente
        for i in range(connections_per_ring):
            agg_idx = (ring_id * connections_per_ring + i) % num_agg_nodes
            agg_node = agg_nodes[agg_idx]

            # Enlace bidireccional: access gateway <-> aggregation
            enlaces.append(Enlace(gateway_node, agg_node, uplink_capacity))
            enlaces.append(Enlace(agg_node, gateway_node, uplink_capacity))

    # 3. Crear capa de agregación (full mesh o anillo)
    # Opción: full mesh entre nodos de agregación
    for i, agg_node_i in enumerate(agg_nodes):
        for agg_node_j in agg_nodes[i+1:]:
            enlaces.append(Enlace(agg_node_i, agg_node_j, agg_capacity))
            enlaces.append(Enlace(agg_node_j, agg_node_i, agg_capacity))

    info = {
        'num_access_rings': num_access_rings,
        'nodes_per_ring': nodes_per_ring,
        'total_access_nodes': total_access_nodes,
        'num_agg_nodes': num_agg_nodes,
        'access_nodes': access_nodes,
        'agg_nodes': agg_nodes,
        'num_enlaces': len(enlaces),
        'access_capacity': access_capacity,
        'uplink_capacity': uplink_capacity,
        'agg_capacity': agg_capacity
    }

    return enlaces, info


def construir_grafo_adyacencia(enlaces: List[Enlace]) -> Dict[int, List[Tuple[int, Enlace]]]:
    """
    Construye un grafo de adyacencia desde la lista de enlaces.
    """
    grafo = {}
    for enlace in enlaces:
        if enlace.source not in grafo:
            grafo[enlace.source] = []
        grafo[enlace.source].append((enlace.target, enlace))
    return grafo


def encontrar_k_paths_bfs(
    source: int,
    target: int,
    enlaces: List[Enlace],
    k: int = 3,
    max_length: int = None
) -> List[List[Enlace]]:
    """
    Encuentra hasta k caminos más cortos entre source y target usando BFS.

    Args:
        source: Nodo origen
        target: Nodo destino
        enlaces: Lista de todos los enlaces
        k: Número máximo de caminos a encontrar
        max_length: Longitud máxima de caminos (en hops)

    Returns:
        Lista de caminos, donde cada camino es una lista de Enlaces
    """
    if source == target:
        return [[]]

    grafo = construir_grafo_adyacencia(enlaces)

    # BFS para encontrar la distancia más corta
    queue = deque([(source, 0)])
    distancias = {source: 0}

    while queue:
        nodo, dist = queue.popleft()
        if nodo == target:
            continue

        if nodo not in grafo:
            continue

        for vecino, _ in grafo[nodo]:
            if vecino not in distancias:
                distancias[vecino] = dist + 1
                queue.append((vecino, dist + 1))

    if target not in distancias:
        return []

    dist_min = distancias[target]

    # Establecer límite de búsqueda
    if max_length is None:
        max_length = dist_min + 3

    # DFS para encontrar todos los caminos
    todos_caminos = []

    def dfs(nodo_actual, camino_actual, visitados):
        if len(camino_actual) > max_length:
            return

        if nodo_actual == target:
            todos_caminos.append(camino_actual[:])
            if len(todos_caminos) >= k * 3:  # Encontrar extra para filtrar después
                return
            return

        if nodo_actual not in grafo:
            return

        for vecino, enlace in grafo[nodo_actual]:
            if vecino not in visitados:
                visitados.add(vecino)
                camino_actual.append(enlace)
                dfs(vecino, camino_actual, visitados)
                camino_actual.pop()
                visitados.remove(vecino)

    visitados = {source}
    dfs(source, [], visitados)

    # Ordenar por longitud y tomar los k más cortos
    todos_caminos.sort(key=len)
    return todos_caminos[:k]


def generar_commodities_estrategicos(
    num_commodities: int,
    info: Dict,
    requirement: float,
    intra_ring_ratio: float = 0.5,
    seed: int = None
) -> List[Tuple[int, int]]:
    """
    Genera pares (source, target) estratégicos para commodities.

    Args:
        num_commodities: Número de commodities a generar
        info: Diccionario con información de la red (de generar_red_acceso_agregacion)
        requirement: Requirement de cada commodity
        intra_ring_ratio: Proporción de commodities intra-ring vs inter-ring (0 a 1)
        seed: Semilla para reproducibilidad

    Returns:
        Lista de tuplas (source, target)
    """
    if seed is not None:
        random.seed(seed)

    access_nodes = info['access_nodes']
    nodes_per_ring = info['nodes_per_ring']
    num_access_rings = info['num_access_rings']

    pares = []
    num_intra_ring = int(num_commodities * intra_ring_ratio)
    num_inter_ring = num_commodities - num_intra_ring

    # 1. Generar commodities intra-ring (dentro del mismo anillo)
    intentos = 0
    max_intentos = num_intra_ring * 100

    while len(pares) < num_intra_ring and intentos < max_intentos:
        ring_id = random.randint(0, num_access_rings - 1)
        ring_start = ring_id * nodes_per_ring
        ring_end = ring_start + nodes_per_ring

        source = random.randint(ring_start, ring_end - 1)
        target = random.randint(ring_start, ring_end - 1)

        if source != target and (source, target) not in pares:
            pares.append((source, target))

        intentos += 1

    # 2. Generar commodities inter-ring (entre diferentes anillos)
    intentos = 0
    max_intentos = num_inter_ring * 100

    while len(pares) < num_commodities and intentos < max_intentos:
        ring_id_1 = random.randint(0, num_access_rings - 1)
        ring_id_2 = random.randint(0, num_access_rings - 1)

        # Asegurar que sean anillos diferentes
        if ring_id_1 == ring_id_2:
            intentos += 1
            continue

        ring_start_1 = ring_id_1 * nodes_per_ring
        ring_end_1 = ring_start_1 + nodes_per_ring

        ring_start_2 = ring_id_2 * nodes_per_ring
        ring_end_2 = ring_start_2 + nodes_per_ring

        source = random.randint(ring_start_1, ring_end_1 - 1)
        target = random.randint(ring_start_2, ring_end_2 - 1)

        if (source, target) not in pares:
            pares.append((source, target))

        intentos += 1

    return pares
