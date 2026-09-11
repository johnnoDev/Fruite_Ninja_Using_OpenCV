import math

def point_line_segment_distance_sq(px, py, x1, y1, x2, y2):
    """
    Calcula la distancia al cuadrado desde el punto (px, py) hasta el segmento de línea (x1,y1)-(x2,y2).
    Se devuelve la distancia al cuadrado para evitar cálculos costosos de raíz cuadrada cuando no son necesarios.
    """
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return (px - x1)**2 + (py - y1)**2

    # Proyectar el punto sobre la línea (parámetro t)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)

    # Limitar t al segmento [0, 1]
    t = max(0, min(1, t))

    # Punto más cercano en el segmento
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    return (px - closest_x)**2 + (py - closest_y)**2

def check_capsule_circle_collision(p1, p2, thickness, center, radius):
    """
    Verifica si una cápsula (segmento de línea p1-p2 con grosor) intersecta un círculo.

    p1, p2: tuplas (x, y)
    center: tupla (x, y)
    thickness: float (radio del extremo de la cápsula)
    radius: float (radio del círculo)
    """
    dist_sq = point_line_segment_distance_sq(center[0], center[1], p1[0], p1[1], p2[0], p2[1])

    # Hay colisión si la distancia < (radio_cápsula + radio_círculo)
    # Nota: ¿'thickness' en este contexto suele ser el ancho total?
    # Supongamos que 'thickness' de entrada es el ancho total, por lo que el radio es thickness/2.
    # Sin embargo, normalmente para una hoja tratamos thickness como el radio del círculo "barrido".
    # Digamos que thickness es el "alcance".
    
    threshold = (thickness + radius) ** 2
    return dist_sq <= threshold
