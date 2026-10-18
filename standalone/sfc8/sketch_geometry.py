"""Planar geometry shared by live previews and native Sketcher commands."""
import math

TOLERANCE = 1e-7


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def arc_through_points(start, middle, end, segments=48):
    """Sample the oriented circular arc passing through three distinct points."""
    if min(distance(start, middle), distance(middle, end), distance(start, end)) <= TOLERANCE:
        raise ValueError("El arco necesita tres puntos distintos.")
    # Work around the first point to keep the determinant stable far from origin.
    bx, by = middle[0] - start[0], middle[1] - start[1]
    cx, cy = end[0] - start[0], end[1] - start[1]
    determinant = 2 * (bx * cy - by * cx)
    scale = max(math.hypot(bx, by), math.hypot(cx, cy))
    if abs(determinant) <= TOLERANCE * scale:
        raise ValueError("Los tres puntos del arco no pueden estar alineados.")
    ux = (cy * (bx * bx + by * by) - by * (cx * cx + cy * cy)) / determinant
    uy = (bx * (cx * cx + cy * cy) - cx * (bx * bx + by * by)) / determinant
    center = (start[0] + ux, start[1] + uy)
    angles = [math.atan2(p[1] - center[1], p[0] - center[0]) for p in (start, middle, end)]
    sweep = (angles[2] - angles[0]) % math.tau
    if (angles[1] - angles[0]) % math.tau > sweep:
        sweep -= math.tau
    radius = math.hypot(ux, uy)
    points = [(center[0] + radius * math.cos(angles[0] + sweep * i / segments), center[1] + radius * math.sin(angles[0] + sweep * i / segments)) for i in range(segments + 1)]
    points[0], points[-1] = tuple(start), tuple(end)
    return points
