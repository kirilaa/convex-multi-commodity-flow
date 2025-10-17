from modelos import Enlace
from typing import List, Tuple, Dict, Set
from collections import deque
import random


def numerar_nodos_fat_tree(k: int) -> Dict[str, range]:
    """
    Esquema de numeración para nodos en fat tree k-ary.

    Para k=8:
    - Hosts: 0-127 (k³/4 = 128 hosts)
    - Edge switches: 128-191 (k²/2 = 32 switches)
    - Aggregation switches: 192-255 (k²/2 = 32 switches)
    - Core switches: 256-271 (k²/4 = 16 switches)
    """
    num_hosts = (k ** 3) // 4
    num_edge = (k ** 2) // 2
    num_agg = (k ** 2) // 2
    num_core = (k ** 2) // 4

    hosts_range = range(0, num_hosts)
    edge_range = range(num_hosts, num_hosts + num_edge)
    agg_range = range(num_hosts + num_edge, num_hosts + num_edge + num_agg)
    core_range = range(num_hosts + num_edge + num_agg, num_hosts + num_edge + num_agg + num_core)

    return {
        'hosts': hosts_range,
        'edge': edge_range,
        'agg': agg_range,
        'core': core_range
    }


def generar_fat_tree(k: int, capacity: float = 100.0) -> Tuple[List[Enlace], Dict]:
    """
    Genera una topología fat tree k-ary.

    Estructura:
    - k pods, cada uno con k/2 edge switches y k/2 aggregation switches
    - Cada edge switch conecta a k/2 hosts
    - Cada edge switch conecta a todos los k/2 aggregation switches de su pod
    - Cada aggregation switch conecta a k/2 core switches
    - Total: (k²/4) core switches

    Returns:
        Tuple de (lista de Enlaces, diccionario con info de nodos)
    """
    if k % 2 != 0:
        raise ValueError("k debe ser par para fat tree")

    nodos = numerar_nodos_fat_tree(k)
    enlaces = []

    # Índices para acceder a los diferentes tipos de switches
    hosts = list(nodos['hosts'])
    edge_switches = list(nodos['edge'])
    agg_switches = list(nodos['agg'])
    core_switches = list(nodos['core'])

    num_pods = k
    switches_per_pod = k // 2
    hosts_per_edge = k // 2

    # Generar enlaces para cada pod
    for pod in range(num_pods):
        # Edge switches para este pod
        edge_start_idx = pod * switches_per_pod
        edge_end_idx = edge_start_idx + switches_per_pod
        pod_edge_switches = edge_switches[edge_start_idx:edge_end_idx]

        # Aggregation switches para este pod
        agg_start_idx = pod * switches_per_pod
        agg_end_idx = agg_start_idx + switches_per_pod
        pod_agg_switches = agg_switches[agg_start_idx:agg_end_idx]

        # 1. Conectar hosts a edge switches
        for i, edge_sw in enumerate(pod_edge_switches):
            host_start_idx = pod * switches_per_pod * hosts_per_edge + i * hosts_per_edge
            for j in range(hosts_per_edge):
                host = hosts[host_start_idx + j]
                # Enlace bidireccional: host <-> edge switch
                enlaces.append(Enlace(host, edge_sw, capacity))
                enlaces.append(Enlace(edge_sw, host, capacity))

        # 2. Conectar edge switches a aggregation switches (dentro del pod)
        for edge_sw in pod_edge_switches:
            for agg_sw in pod_agg_switches:
                # Enlace bidireccional: edge <-> aggregation
                enlaces.append(Enlace(edge_sw, agg_sw, capacity))
                enlaces.append(Enlace(agg_sw, edge_sw, capacity))

    # 3. Conectar aggregation switches a core switches
    # Cada aggregation switch i en posición j del pod se conecta a k/2 core switches
    for pod in range(num_pods):
        agg_start_idx = pod * switches_per_pod
        for j in range(switches_per_pod):
            agg_sw = agg_switches[agg_start_idx + j]
            # Este agg switch se conecta a core switches en el rango [j*k/2, (j+1)*k/2)
            core_start = j * switches_per_pod
            core_end = core_start + switches_per_pod
            for core_sw in core_switches[core_start:core_end]:
                # Enlace bidireccional: aggregation <-> core
                enlaces.append(Enlace(agg_sw, core_sw, capacity))
                enlaces.append(Enlace(core_sw, agg_sw, capacity))

    info = {
        'k': k,
        'num_hosts': len(hosts),
        'num_edge': len(edge_switches),
        'num_agg': len(agg_switches),
        'num_core': len(core_switches),
        'num_enlaces': len(enlaces),
        'nodos': nodos
    }

    return enlaces, info


def construir_grafo_adyacencia(enlaces: List[Enlace]) -> Dict[int, List[Tuple[int, Enlace]]]:
    """
    Construye un grafo de adyacencia desde la lista de enlaces.

    Returns:
        Dict donde cada nodo mapea a lista de (vecino, enlace) tuplas
    """
    grafo = {}
    for enlace in enlaces:
        if enlace.source not in grafo:
            grafo[enlace.source] = []
        grafo[enlace.source].append((enlace.target, enlace))
    return grafo


def encontrar_k_paths_mas_cortos(
    source: int,
    target: int,
    enlaces: List[Enlace],
    k: int = 3
) -> List[List[Enlace]]:
    """
    Encuentra los k caminos más cortos entre source y target usando BFS modificado.

    Algoritmo:
    1. BFS para encontrar la distancia más corta
    2. BFS nuevamente para encontrar todos los caminos de longitud mínima
    3. Si hay menos de k caminos de longitud mínima, buscar caminos de longitud mínima+1, etc.

    Returns:
        Lista de caminos, donde cada camino es una lista de Enlaces
    """
    if source == target:
        return [[]]

    grafo = construir_grafo_adyacencia(enlaces)

    # BFS para encontrar distancia más corta
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
        return []  # No hay camino

    dist_min = distancias[target]

    # Encontrar todos los caminos usando DFS con límite de longitud
    todos_caminos = []
    max_length_to_explore = dist_min + 2  # Explorar hasta 2 hops más que el mínimo

    def dfs(nodo_actual, camino_actual, longitud):
        if longitud > max_length_to_explore:
            return

        if nodo_actual == target:
            todos_caminos.append(camino_actual[:])
            return

        if nodo_actual not in grafo:
            return

        for vecino, enlace in grafo[nodo_actual]:
            # Evitar ciclos
            if vecino in [e.source for e in camino_actual]:
                continue

            camino_actual.append(enlace)
            dfs(vecino, camino_actual, longitud + 1)
            camino_actual.pop()

    dfs(source, [], 0)

    # Ordenar por longitud y tomar los primeros k
    todos_caminos.sort(key=len)
    return todos_caminos[:k]


def generar_pares_aleatorios(num_hosts: int, num_flows: int, seed: int = None) -> List[Tuple[int, int]]:
    """
    Genera pares aleatorios (source, target) de hosts para los flujos.

    Args:
        num_hosts: Número total de hosts (deben estar numerados 0 a num_hosts-1)
        num_flows: Número de pares a generar
        seed: Semilla para reproducibilidad

    Returns:
        Lista de tuplas (source, target)
    """
    if seed is not None:
        random.seed(seed)

    pares = []
    intentos = 0
    max_intentos = num_flows * 100

    while len(pares) < num_flows and intentos < max_intentos:
        source = random.randint(0, num_hosts - 1)
        target = random.randint(0, num_hosts - 1)

        if source != target and (source, target) not in pares:
            pares.append((source, target))

        intentos += 1

    if len(pares) < num_flows:
        print(f"Advertencia: Solo se pudieron generar {len(pares)} pares únicos de {num_flows} solicitados")

    return pares
