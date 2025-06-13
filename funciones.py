from modelos import Enlace, Commodity
from collections import defaultdict

def distribuir_trafico_uniforme(commodity):
    num_paths = len(commodity.paths)
    if num_paths == 0:
        raise ValueError(f"{commodity.name} no tiene paths definidos.")

    trafico_unitario = commodity.requirement / num_paths
    for path in commodity.paths:
        path.trafico = trafico_unitario

def f_prima(capacity, total_flow):
    p = 0.99
    if total_flow > p * capacity:
        return 1 / (capacity * (1 - p) ** 2)
    else:
        return capacity / (capacity - total_flow) ** 2

def calcular_flujo_por_enlace(commodities):
    flujo_por_enlace = defaultdict(float)
    for commodity in commodities:
        for path in commodity.paths:
            for enlace in path.enlaces:
                flujo_por_enlace[enlace] += path.trafico
    return dict(flujo_por_enlace)

def calcular_coste_por_enlace(flujo_por_enlace):
    costes = {}
    for enlace, flujo in flujo_por_enlace.items():
        costes[enlace] = f_prima(enlace.capacity, flujo)
    return costes

def calcular_coste_total_por_path(commodities, flujo_por_enlace):
    costes_path = {}
    for commodity in commodities:
        #print(f"\nCostes por path para {commodity.name}:")
        for i, path in enumerate(commodity.paths, start=1):
            enlaces_path = [(e.source, e.target) for e in path.enlaces]
            #print(f"\nPath {i}: Enlaces = {enlaces_path}")
            
            coste_path = 0.0
            for enlace in path.enlaces:
                flujo = flujo_por_enlace[enlace]
                coste_enlace = f_prima(enlace.capacity, flujo)
                #print(f" - Enlace ({enlace.source}->{enlace.target}): capacidad={enlace.capacity}, flujo={flujo:.4f}, coste={coste_enlace:.4f}")
                coste_path += coste_enlace

            #print(f" → Coste total del Path {i} = {coste_path:.4f}")
            costes_path[(commodity, i)] = coste_path
    return costes_path



def seleccionar_path_minimo_coste(commodities, costes_path_anterior):
    shortest_paths = {} 
    for commodity in commodities:
        paths_costes = {
            path_id: coste
            for (commodity_iter, path_id), coste in costes_path_anterior.items()
            if commodity_iter == commodity
        }
        
        if paths_costes:
            path_minimo_id = min(paths_costes, key=paths_costes.get)
            shortest_paths[commodity] = path_minimo_id
    
    return shortest_paths

def calculo_del_trafico_para_la_siguiente_iteracion(
    t: int,
    x_kp_actual: float,
    H_kp: float, 
    d_kp: float, 
    d_kbeta: float
) -> float:
    termino_adaptacion = x_kp_actual - (0.001 / H_kp) * (d_kp - d_kbeta)
    termino_positivo = max(0.0, termino_adaptacion)
    nuevo_trafico = termino_positivo
    return nuevo_trafico

def f_double_prima(enlace: Enlace, flujo_total: float) -> float:
    p = 0.99
    if flujo_total > p * enlace.capacity:
        return 0.0
    else:
        return (2 * enlace.capacity) / (enlace.capacity - flujo_total) ** 3

def calcular_H_kp(path_actual, mejor_path, flujo_por_enlace_anterior):
    enlaces_actual = set(path_actual.enlaces)
    enlaces_mejor = set(mejor_path.enlaces)
    L_kp = enlaces_actual.symmetric_difference(enlaces_mejor)
    
    #print("\n--- Debug H_kp ---")
    #print(f"Enlaces Path actual: [{', '.join(f'({e.source}->{e.target})' for e in enlaces_actual)}]")
    #print(f"Enlaces Mejor path: [{', '.join(f'({e.source}->{e.target})' for e in enlaces_mejor)}]")
    #print(f"Diferencia simétrica (L_kp): [{', '.join(f'({e.source}->{e.target})' for e in L_kp)}]")
    
    H_kp = 0.0
    for enlace in L_kp:
        flujo = flujo_por_enlace_anterior.get(enlace, 0.0)
        f_dp = f_double_prima(enlace, flujo)
        #print(f"Enlace ({enlace.source}->{enlace.target}): capacidad={enlace.capacity}, flujo={flujo:.4f}, f''={f_dp:.6f}")
        H_kp += f_dp
    
    #print(f"H_kp final: {H_kp:.6f}\n")
    return H_kp


def funcion_principal(commodities):
    iteraciones = {
        "flujo_total": [],
        "costes_path": [],
        "shortest_paths": []
    }

    for i in range(200):    # Número de iteraciones
        print(f"\n{'='*40}\nIteración {i}:\n{'='*40}")

        if i == 0:
            for commodity in commodities:
                distribuir_trafico_uniforme(commodity)
            print("\nVerificación de tráfico inicial:")
            for commodity in commodities:
                traficos = [f"{path.trafico:.4f}" for path in commodity.paths]
                print(f"{commodity.name}: {traficos}")
        else:
            for commodity in commodities:
                costes_commodity = {path_id: coste 
                                   for (comm, path_id), coste in iteraciones["costes_path"][i-1].items() 
                                   if comm == commodity}
                if not costes_commodity:
                    continue
                path_minimo_id = min(costes_commodity, key=costes_commodity.get)
                d_kbeta = costes_commodity[path_minimo_id]

                suma_flujo_otros = 0.0
                for path_id, coste_actual in costes_commodity.items():
                    if path_id == path_minimo_id:
                        continue
                    path_actual = commodity.paths[path_id - 1]
                    x_kp_actual = path_actual.trafico
                    t = i
                    mejor_path = commodity.paths[path_minimo_id - 1]
                    H_kp = calcular_H_kp(
                        path_actual=path_actual,
                        mejor_path=mejor_path,
                        flujo_por_enlace_anterior=iteraciones["flujo_total"][i-1]
                    )
                    d_kp = coste_actual
                    
                    print(f"\nActualizando {commodity.name} Path {path_id}:")
                    print(f"• t: {t}")
                    print(f"• x_kp_actual: {x_kp_actual:.4f}")
                    print(f"• H_kp: {H_kp:.4f}")
                    print(f"• d_kp: {d_kp:.4f}")
                    print(f"• d_kbeta: {d_kbeta:.4f}")

                    nuevo_trafico = calculo_del_trafico_para_la_siguiente_iteracion(
                        t=i, 
                        x_kp_actual=x_kp_actual, 
                        H_kp=H_kp, 
                        d_kp=d_kp, 
                        d_kbeta=d_kbeta
                    )
                    print(f"-> Nuevo tráfico: {nuevo_trafico:.4f}")
                    commodity.paths[path_id-1].trafico = nuevo_trafico
                    suma_flujo_otros += nuevo_trafico

                flujo_shortest_path = commodity.requirement - suma_flujo_otros
                commodity.paths[path_minimo_id-1].trafico = max(0.0, flujo_shortest_path)
                print(f"\n{commodity.name} - Path {path_minimo_id} (shortest) actualizado:")
                print(f"Flujo total requirement: {commodity.requirement:.4f}")
                print(f"Suma otros paths: {suma_flujo_otros:.4f}")
                print(f"Flujo asignado: {flujo_shortest_path:.4f}")

        flujo_total = calcular_flujo_por_enlace(commodities)
        costes_path = calcular_coste_total_por_path(commodities, flujo_total)
        shortest_paths = seleccionar_path_minimo_coste(commodities, costes_path)

        iteraciones["flujo_total"].append(flujo_total)
        iteraciones["costes_path"].append(costes_path)
        iteraciones["shortest_paths"].append(shortest_paths)

        print("\nCantidad de flujo que pasa por cada enlace:")
        for enlace, flujo in flujo_total.items():
            print(f"{enlace}: Flujo = {flujo:.4f}")

        print("\nCoste total de cada path en función del commodity:")
        for (commodity, i), coste in costes_path.items():
            print(f"{commodity.name}, Path {i}: Coste = {coste:.4f}")
            
        print("\nPath de menor coste para cada commodity:")
        for commodity, path_id in shortest_paths.items():
            print(f"{commodity.name}: Path {path_id} con coste {costes_path[(commodity, path_id)]:.4f}")

    return iteraciones