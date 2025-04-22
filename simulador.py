from modelos import Enlace, Commodity, Path
from funciones import funcion_principal

# Definir enlaces
e1 = Enlace(1, 2, 5)
e2 = Enlace(1, 4, 3)
e3 = Enlace(1, 3, 4)
e4 = Enlace(2, 4, 3)
e5 = Enlace(3, 4, 1)

# Definir commodities sin paths de momento
k1 = Commodity(1, 4, 4)
k2 = Commodity(2, 4, 3)

# Asociar paths a cada commodity como objetos Path
k1.add_path(Path(k1, [e1, e4]))
k1.add_path(Path(k1, [e2]))
k1.add_path(Path(k1, [e3, e5]))

k2.add_path(Path(k2, [e4]))
k2.add_path(Path(k2, [e1, e2]))
k2.add_path(Path(k2, [e1, e3, e5]))

# Ejecutar simulación
funcion_principal([k1, k2])
