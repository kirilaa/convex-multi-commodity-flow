from modelos import Commodity, Path
from funciones import funcion_principal
from fat_tree_topology import (
    generar_fat_tree,
    encontrar_k_paths_mas_cortos,
    generar_pares_aleatorios
)
import time


def main():
    print("="*60)
    print("SIMULADOR DE FAT TREE CON 100 FLUJOS")
    print("="*60)

    # Parámetros de la simulación
    k = 8  # Fat tree k=8 -> 128 hosts
    link_capacity = 100.0
    num_flows = 100
    flow_requirement = 50.0  # Mitad del ancho de banda del enlace
    num_paths_per_flow = 3
    random_seed = 42

    print(f"\nParámetros:")
    print(f"  - Topología: Fat tree k={k}")
    print(f"  - Capacidad de enlaces: {link_capacity}")
    print(f"  - Número de flujos: {num_flows}")
    print(f"  - Requirement por flujo: {flow_requirement} (50% de capacidad)")
    print(f"  - Paths por flujo: {num_paths_per_flow}")
    print(f"  - Semilla aleatoria: {random_seed}")

    # Generar topología fat tree
    print(f"\nGenerando topología fat tree k={k}...")
    start_time = time.time()
    enlaces, info = generar_fat_tree(k, link_capacity)
    topology_time = time.time() - start_time

    print(f"  ✓ Topología generada en {topology_time:.2f}s")
    print(f"  - Hosts: {info['num_hosts']}")
    print(f"  - Edge switches: {info['num_edge']}")
    print(f"  - Aggregation switches: {info['num_agg']}")
    print(f"  - Core switches: {info['num_core']}")
    print(f"  - Total enlaces: {info['num_enlaces']}")

    # Generar pares aleatorios de flujos
    print(f"\nGenerando {num_flows} pares aleatorios de flujos...")
    pares_flujos = generar_pares_aleatorios(info['num_hosts'], num_flows, random_seed)
    print(f"  ✓ {len(pares_flujos)} pares generados")

    # Crear commodities y encontrar paths
    print(f"\nCreando commodities y encontrando paths...")
    commodities = []
    start_time = time.time()

    for idx, (source, target) in enumerate(pares_flujos):
        # Crear commodity
        commodity = Commodity(source, target, flow_requirement)

        # Encontrar k paths más cortos
        paths_enlaces = encontrar_k_paths_mas_cortos(
            source, target, enlaces, num_paths_per_flow
        )

        if not paths_enlaces:
            print(f"  ⚠ Advertencia: No se encontraron paths para flujo {source}→{target}")
            continue

        # Agregar paths al commodity
        for path_enlaces in paths_enlaces:
            path = Path(commodity, path_enlaces, trafico=0.0)
            commodity.add_path(path)

        commodities.append(commodity)

        # Progreso
        if (idx + 1) % 20 == 0:
            print(f"  - Procesados {idx + 1}/{num_flows} flujos...")

    paths_time = time.time() - start_time
    print(f"  ✓ {len(commodities)} commodities creados en {paths_time:.2f}s")

    # Estadísticas de paths
    total_paths = sum(len(c.paths) for c in commodities)
    avg_paths = total_paths / len(commodities) if commodities else 0
    print(f"  - Total paths: {total_paths}")
    print(f"  - Promedio paths por commodity: {avg_paths:.2f}")

    # Ejecutar simulación
    print(f"\n{'='*60}")
    print("INICIANDO OPTIMIZACIÓN")
    print(f"{'='*60}\n")

    start_time = time.time()
    resultados = funcion_principal(commodities)
    simulation_time = time.time() - start_time

    print(f"\n{'='*60}")
    print("SIMULACIÓN COMPLETADA")
    print(f"{'='*60}")
    print(f"Tiempo total: {simulation_time:.2f}s")
    print(f"Iteraciones ejecutadas: {len(resultados['flujo_total'])}")

    # Análisis final
    print(f"\n{'='*60}")
    print("ANÁLISIS DE RESULTADOS FINALES")
    print(f"{'='*60}")

    if resultados['flujo_total']:
        ultima_iteracion = resultados['flujo_total'][-1]

        # Enlaces con mayor utilización
        enlaces_ordenados = sorted(
            ultima_iteracion.items(),
            key=lambda x: x[1] / x[0].capacity,
            reverse=True
        )

        print("\nTop 10 enlaces con mayor utilización:")
        for i, (enlace, flujo) in enumerate(enlaces_ordenados[:10], 1):
            utilizacion = (flujo / enlace.capacity) * 100
            print(f"  {i}. Enlace {enlace.source}→{enlace.target}: "
                  f"{flujo:.2f}/{enlace.capacity:.2f} ({utilizacion:.1f}%)")

        # Estadísticas de costes por path
        costes_finales = resultados['costes_path'][-1]
        valores_costes = list(costes_finales.values())
        if valores_costes:
            print(f"\nEstadísticas de costes de paths:")
            print(f"  - Coste mínimo: {min(valores_costes):.4f}")
            print(f"  - Coste máximo: {max(valores_costes):.4f}")
            print(f"  - Coste promedio: {sum(valores_costes)/len(valores_costes):.4f}")

        # Verificar flow conservation
        print(f"\nVerificación de conservación de flujo:")
        all_satisfied = True
        for commodity in commodities[:5]:  # Mostrar solo los primeros 5
            total_trafico = sum(path.trafico for path in commodity.paths)
            diff = abs(total_trafico - commodity.requirement)
            status = "✓" if diff < 0.01 else "✗"
            print(f"  {status} {commodity.name}: "
                  f"{total_trafico:.4f}/{commodity.requirement:.4f}")
            if diff >= 0.01:
                all_satisfied = False

        if all_satisfied:
            print(f"  ✓ Todos los commodities satisfacen sus requirements")
        else:
            print(f"  ⚠ Algunos commodities no satisfacen completamente sus requirements")


if __name__ == "__main__":
    main()
