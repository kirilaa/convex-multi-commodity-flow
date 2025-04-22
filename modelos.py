from typing import List


class Enlace:
    def __init__(self, source: int, target: int, capacity: float):
        self.source = source
        self.target = target
        self.capacity = capacity

    def __repr__(self):
        return f"Enlace con inicio en {self.source}, final en {self.target}, capacidad = {self.capacity}"

    def __eq__(self, other):
        return isinstance(other, Enlace) and \
            self.source == other.source and \
            self.target == other.target and \
            self.capacity == other.capacity

    def __hash__(self):
        return hash((self.source, self.target, self.capacity))


class Path:
    contador = 1  # para asignar IDs únicos si quieres diferenciarlos

    def __init__(self, commodity, enlaces: List['Enlace'], trafico: float = 0.0):
        self.id = Path.contador
        Path.contador += 1

        self.commodity = commodity  # Commodity al que pertenece este path
        self.enlaces = enlaces      # Lista de Enlace
        self.trafico = trafico      # Tráfico asignado a este path (puede ser actualizado)

    def nodos(self):
        """Devuelve la secuencia de nodos desde el source hasta el target del path."""
        if not self.enlaces:
            return []
        nodos = [self.enlaces[0].source]
        for enlace in self.enlaces:
            nodos.append(enlace.target)
        return nodos

    def __repr__(self):
        nodos_str = " → ".join(str(n) for n in self.nodos())
        return (f"Path {self.id} para {self.commodity.name}, "
                f"nodos: {nodos_str}, tráfico asignado: {self.trafico}")


class Commodity:
    def __init__(self, source: int, target: int, requirement: float):
        self.source = source
        self.target = target
        self.requirement = requirement
        self.paths: List['Path'] = []  # se rellenará después
        self.name = f"Commodity de {source} -> {target}"

    def __repr__(self):
        return f"Commodity({self.source} → {self.target}, req: {self.requirement})"

    def __eq__(self, other):
        return isinstance(other, Commodity) and \
               self.source == other.source and \
               self.target == other.target and \
               self.requirement == other.requirement

    def __hash__(self):
        return hash((self.source, self.target, self.requirement))

    def add_path(self, path: 'Path'):
        self.paths.append(path)

    def resumen_paths(self):
        return "\n".join(repr(path) for path in self.paths)
        
