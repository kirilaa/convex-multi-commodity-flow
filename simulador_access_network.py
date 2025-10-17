from modelos import Commodity, Path
from funciones import funcion_principal
from ring_topology import (
    generar_red_acceso_agregacion,
    encontrar_k_paths_bfs,
    generar_commodities_estrategicos
)
import time


def main():
    print("="*70)
    print("SIMULADOR DE RED DE ACCESO CON ANILLOS")
    print("="*70)

    # Parámetros de la red
    num_access_rings = 20
    nodes_per_ring = 10
    num_agg_nodes = 30

    # Capacidades (bottleneck en acceso)
    access_capacity = 50.0      # Baja capacidad - bottleneck
    uplink_capacity = 100.0     # Capacidad media
    agg_capacity = 200.0        # Alta capacidad

    # Parámetros de tráfico
    num_commodities = 100
    intra_ring_ratio = 0.5      # 50% tráfico intra-ring, 50% inter-ring

    # Calcular requirement para exhaust 100% de enlaces de acceso
    # Cada anillo tiene nodes_per_ring enlaces, cada enlace es bidireccional
    enlaces_por_anillo = nodes_per_ring
    total_enlaces_acceso = num_access_rings * enlaces_por_anillo
    capacidad_total_acceso = total_enlaces_acceso * access_capacity

    # Para exhaustar al 100%, el tráfico total debe igualar la capacidad
    # Pero cada flujo usa múltiples enlaces, así que usamos un factor
    # Comenzamos con requirement que en agregado sea ~100% de capacidad
    requirement_per_commodity = capacidad_total_acceso / num_commodities

    print(f"\nParámetros de la red:")
    print(f"  - Anillos de acceso: {num_access_rings}")
    print(f"  - Nodos por anillo: {nodes_per_ring}")
    print(f"  - Total nodos de acceso: {num_access_rings * nodes_per_ring}")
    print(f"  - Nodos de agregación: {num_agg_nodes}")
    print(f"  - Capacidad enlaces acceso: {access_capacity}")
    print(f"  - Capacidad enlaces uplink: {uplink_capacity}")
    print(f"  - Capacidad enlaces agregación: {agg_capacity}")

    print(f"\nParámetros de tráfico:")
    print(f"  - Número de commodities: {num_commodities}")
    print(f"  - Ratio intra-ring: {intra_ring_ratio:.0%}")
    print(f"  - Requirement por commodity: {requirement_per_commodity:.2f}")
    print(f"  - Capacidad total acceso: {capacidad_total_acceso:.2f}")
    print(f"  - Tráfico total objetivo: {num_commodities * requirement_per_commodity:.2f}")

    # Generar topología
    print(f"\nGenerando topología de red de acceso...")
    start_time = time.time()
    enlaces, info = generar_red_acceso_agregacion(
        num_access_rings=num_access_rings,
        nodes_per_ring=nodes_per_ring,
        num_agg_nodes=num_agg_nodes,
        access_capacity=access_capacity,
        uplink_capacity=uplink_capacity,
        agg_capacity=agg_capacity,
        connections_per_ring=2  # Cada anillo conecta a 2 nodos de agregación
    )
    topology_time = time.time() - start_time

    print(f"  ✓ Topología generada en {topology_time:.2f}s")
    print(f"  - Total nodos: {info['total_access_nodes'] + info['num_agg_nodes']}")
    print(f"  - Nodos de acceso: {info['total_access_nodes']}")
    print(f"  - Nodos de agregación: {info['num_agg_nodes']}")
    print(f"  - Total enlaces: {info['num_enlaces']}")

    # Calcular distribución de enlaces
    num_enlaces_acceso = num_access_rings * nodes_per_ring * 2  # bidireccional
    num_enlaces_uplink = num_access_rings * 2 * 2 * 2  # 2 gateways × 2 conexiones × 2 direcciones
    num_enlaces_agg = info['num_enlaces'] - num_enlaces_acceso - num_enlaces_uplink

    print(f"  - Enlaces en anillos de acceso: {num_enlaces_acceso}")
    print(f"  - Enlaces uplink (2 gateways): {num_enlaces_uplink}")
    print(f"  - Enlaces en agregación: {num_enlaces_agg}")

    # Generar commodities estratégicos
    print(f"\nGenerando {num_commodities} commodities...")
    pares_commodities = generar_commodities_estrategicos(
        num_commodities=num_commodities,
        info=info,
        requirement=requirement_per_commodity,
        intra_ring_ratio=intra_ring_ratio,
        seed=42
    )
    print(f"  ✓ {len(pares_commodities)} pares generados")

    # Analizar distribución
    num_intra = 0
    num_inter = 0
    for source, target in pares_commodities:
        source_ring = source // nodes_per_ring
        target_ring = target // nodes_per_ring
        if source_ring == target_ring:
            num_intra += 1
        else:
            num_inter += 1

    print(f"  - Commodities intra-ring: {num_intra}")
    print(f"  - Commodities inter-ring: {num_inter}")

    # Crear commodities y encontrar paths
    print(f"\nCreando commodities y encontrando paths...")
    commodities = []
    start_time = time.time()

    for idx, (source, target) in enumerate(pares_commodities):
        # Crear commodity
        commodity = Commodity(source, target, requirement_per_commodity)

        # Encontrar hasta 3 paths
        paths_enlaces = encontrar_k_paths_bfs(
            source, target, enlaces, k=3, max_length=10
        )

        if not paths_enlaces:
            print(f"  ⚠ Advertencia: No se encontraron paths para commodity {source}→{target}")
            continue

        # Limitar a máximo 3 paths para eficiencia
        for path_enlaces in paths_enlaces[:3]:
            path = Path(commodity, path_enlaces, trafico=0.0)
            commodity.add_path(path)

        commodities.append(commodity)

        # Progreso
        if (idx + 1) % 20 == 0:
            print(f"  - Procesados {idx + 1}/{num_commodities} commodities...")

    paths_time = time.time() - start_time
    print(f"  ✓ {len(commodities)} commodities creados en {paths_time:.2f}s")

    # Estadísticas de paths
    total_paths = sum(len(c.paths) for c in commodities)
    avg_paths = total_paths / len(commodities) if commodities else 0
    print(f"  - Total paths: {total_paths}")
    print(f"  - Promedio paths por commodity: {avg_paths:.2f}")

    # Ejecutar simulación
    print(f"\n{'='*70}")
    print("INICIANDO OPTIMIZACIÓN")
    print(f"{'='*70}\n")

    start_time = time.time()
    resultados = funcion_principal(commodities)
    simulation_time = time.time() - start_time

    print(f"\n{'='*70}")
    print("SIMULACIÓN COMPLETADA")
    print(f"{'='*70}")
    print(f"Tiempo total: {simulation_time:.2f}s")
    print(f"Iteraciones ejecutadas: {len(resultados['flujo_total'])}")

    # Análisis final
    print(f"\n{'='*70}")
    print("ANÁLISIS DE RESULTADOS FINALES")
    print(f"{'='*70}")

    if resultados['flujo_total']:
        ultima_iteracion = resultados['flujo_total'][-1]

        # Separar enlaces por tipo
        enlaces_acceso = []
        enlaces_uplink = []
        enlaces_agg = []

        for enlace, flujo in ultima_iteracion.items():
            # Enlaces de acceso: ambos nodos < total_access_nodes
            if enlace.source < info['total_access_nodes'] and enlace.target < info['total_access_nodes']:
                enlaces_acceso.append((enlace, flujo))
            # Enlaces de agregación: ambos nodos >= total_access_nodes
            elif enlace.source >= info['total_access_nodes'] and enlace.target >= info['total_access_nodes']:
                enlaces_agg.append((enlace, flujo))
            # Enlaces uplink: cruzan entre capas
            else:
                enlaces_uplink.append((enlace, flujo))

        # Análisis por capa
        print("\n--- CAPA DE ACCESO (Bottleneck) ---")
        if enlaces_acceso:
            enlaces_acceso_sorted = sorted(enlaces_acceso, key=lambda x: x[1]/x[0].capacity, reverse=True)
            utilizaciones_acceso = [flujo/enlace.capacity for enlace, flujo in enlaces_acceso]
            avg_util = sum(utilizaciones_acceso) / len(utilizaciones_acceso)

            print(f"Enlaces de acceso: {len(enlaces_acceso)}")
            print(f"Utilización promedio: {avg_util*100:.1f}%")
            print(f"Utilización máxima: {max(utilizaciones_acceso)*100:.1f}%")
            print(f"Utilización mínima: {min(utilizaciones_acceso)*100:.1f}%")

            print(f"\nTop 10 enlaces de acceso con mayor utilización:")
            for i, (enlace, flujo) in enumerate(enlaces_acceso_sorted[:10], 1):
                util = (flujo / enlace.capacity) * 100
                print(f"  {i}. Enlace {enlace.source}→{enlace.target}: "
                      f"{flujo:.2f}/{enlace.capacity:.2f} ({util:.1f}%)")

        print("\n--- ENLACES UPLINK ---")
        if enlaces_uplink:
            enlaces_uplink_sorted = sorted(enlaces_uplink, key=lambda x: x[1]/x[0].capacity, reverse=True)
            utilizaciones_uplink = [flujo/enlace.capacity for enlace, flujo in enlaces_uplink]
            avg_util = sum(utilizaciones_uplink) / len(utilizaciones_uplink)

            print(f"Enlaces uplink: {len(enlaces_uplink)}")
            print(f"Utilización promedio: {avg_util*100:.1f}%")
            print(f"Utilización máxima: {max(utilizaciones_uplink)*100:.1f}%")

        print("\n--- CAPA DE AGREGACIÓN ---")
        if enlaces_agg:
            utilizaciones_agg = [flujo/enlace.capacity for enlace, flujo in enlaces_agg if flujo > 0]
            if utilizaciones_agg:
                avg_util = sum(utilizaciones_agg) / len(utilizaciones_agg)
                print(f"Enlaces de agregación activos: {len(utilizaciones_agg)}/{len(enlaces_agg)}")
                print(f"Utilización promedio: {avg_util*100:.1f}%")
                print(f"Utilización máxima: {max(utilizaciones_agg)*100:.1f}%")

        # Análisis de Gateways (Dual-Gateway)
        print("\n--- ANÁLISIS DE GATEWAYS (Dual-Gateway) ---")
        if 'gateway_info' in info:
            gateway_stats = []

            for gw_info in info['gateway_info']:
                ring_id = gw_info['ring_id']
                gw1_node = gw_info['gateway_1']
                gw2_node = gw_info['gateway_2']

                # Calcular flujo a través de cada gateway
                gw1_flujo = 0.0
                gw2_flujo = 0.0

                for enlace, flujo in ultima_iteracion.items():
                    # Gateway 1: enlaces salientes desde gw1_node
                    if enlace.source == gw1_node and enlace.target >= info['total_access_nodes']:
                        gw1_flujo += flujo
                    # Gateway 2: enlaces salientes desde gw2_node
                    if enlace.source == gw2_node and enlace.target >= info['total_access_nodes']:
                        gw2_flujo += flujo

                # Capacidad total de cada gateway
                gw_capacity = info['connections_per_gateway'] * uplink_capacity

                gw1_util = gw1_flujo / gw_capacity if gw_capacity > 0 else 0
                gw2_util = gw2_flujo / gw_capacity if gw_capacity > 0 else 0

                # Load balance ratio
                if gw2_util > 0:
                    balance_ratio = gw1_util / gw2_util
                else:
                    balance_ratio = float('inf') if gw1_util > 0 else 1.0

                gateway_stats.append({
                    'ring_id': ring_id,
                    'gw1_flujo': gw1_flujo,
                    'gw2_flujo': gw2_flujo,
                    'gw1_util': gw1_util,
                    'gw2_util': gw2_util,
                    'balance_ratio': balance_ratio,
                    'gw_capacity': gw_capacity
                })

            # Estadísticas generales
            gw1_utils = [gs['gw1_util'] for gs in gateway_stats]
            gw2_utils = [gs['gw2_util'] for gs in gateway_stats]
            balance_ratios = [gs['balance_ratio'] for gs in gateway_stats if gs['balance_ratio'] != float('inf')]

            avg_gw1_util = sum(gw1_utils) / len(gw1_utils) if gw1_utils else 0
            avg_gw2_util = sum(gw2_utils) / len(gw2_utils) if gw2_utils else 0
            avg_balance = sum(balance_ratios) / len(balance_ratios) if balance_ratios else 0

            balanced_rings = sum(1 for gs in gateway_stats if 0.8 <= gs['balance_ratio'] <= 1.25)

            print(f"Total anillos con dual-gateway: {len(gateway_stats)}")
            print(f"Utilización promedio Gateway 1: {avg_gw1_util*100:.1f}%")
            print(f"Utilización promedio Gateway 2: {avg_gw2_util*100:.1f}%")
            print(f"Balance promedio (GW1/GW2): {avg_balance:.2f}")
            print(f"Anillos con carga balanceada (ratio 0.8-1.25): {balanced_rings}/{len(gateway_stats)}")

            # Mostrar top 5 anillos con mayor desbalance
            gateway_stats_sorted = sorted(gateway_stats, key=lambda x: abs(x['balance_ratio'] - 1.0), reverse=True)
            print(f"\nTop 5 anillos con mayor desbalance de carga:")
            for i, gs in enumerate(gateway_stats_sorted[:5], 1):
                print(f"  {i}. Ring {gs['ring_id']}:")
                print(f"     GW1 (nodo {info['gateway_info'][gs['ring_id']]['gateway_1']}): "
                      f"{gs['gw1_flujo']:.2f}/{gs['gw_capacity']:.2f} ({gs['gw1_util']*100:.1f}%)")
                print(f"     GW2 (nodo {info['gateway_info'][gs['ring_id']]['gateway_2']}): "
                      f"{gs['gw2_flujo']:.2f}/{gs['gw_capacity']:.2f} ({gs['gw2_util']*100:.1f}%)")
                print(f"     Balance ratio: {gs['balance_ratio']:.2f}")

        # Verificar flow conservation
        print(f"\n--- CONSERVACIÓN DE FLUJO ---")
        all_satisfied = True
        violations = []

        for commodity in commodities:
            total_trafico = sum(path.trafico for path in commodity.paths)
            diff = abs(total_trafico - commodity.requirement)
            if diff >= 0.01:
                all_satisfied = False
                violations.append((commodity, total_trafico, diff))

        if all_satisfied:
            print(f"  ✓ Todos los {len(commodities)} commodities satisfacen sus requirements")
        else:
            print(f"  ⚠ {len(violations)} commodities no satisfacen completamente sus requirements")
            print(f"\nPrimeros 5 violations:")
            for commodity, trafico, diff in violations[:5]:
                print(f"  - {commodity.name}: {trafico:.4f}/{commodity.requirement:.4f} (diff: {diff:.4f})")


if __name__ == "__main__":
    main()
