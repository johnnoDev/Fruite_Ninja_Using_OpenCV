import math

def point_line_segment_distance_sq(px, py, x1, y1, x2, y2):
    """
    Calculates the squared distance from point (px, py) to the line segment (x1,y1)-(x2,y2).
    Squared distance is returned to avoid expensive sqrt calculations when not needed.
    """
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        return (px - x1)**2 + (py - y1)**2

    # Project point onto line (parameter t)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)

    # Clamp t to segment [0, 1]
    t = max(0, min(1, t))

    # Closest point on segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    return (px - closest_x)**2 + (py - closest_y)**2

def check_capsule_circle_collision(p1, p2, thickness, center, radius):
    """
    Checks if a capsule (line segment p1-p2 with thickness) intersects a circle.
    
    p1, p2: (x, y) tuples
    center: (x, y) tuple
    thickness: float (radius of the capsule end)
    radius: float (radius of the circle)
    """
    dist_sq = point_line_segment_distance_sq(center[0], center[1], p1[0], p1[1], p2[0], p2[1])
    
    # Collision if distance < (capsule_radius + circle_radius)
    # Note: 'thickness' in this context is usually the total width? 
    # Let's assume input 'thickness' is the total width, so radius is thickness/2.
    # However, usually for a blade, we treat thickness as the radius of the "swept" circle.
    # Let's say thickness is the "reach".
    
    threshold = (thickness + radius) ** 2
    return dist_sq <= threshold
