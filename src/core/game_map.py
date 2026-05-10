from src.core.constants import MAP_RADIUS

def create_hex_map():
    hexes = []
    for q in range(-MAP_RADIUS, MAP_RADIUS + 1):
        for r in range(-MAP_RADIUS, MAP_RADIUS + 1):
            if abs(q + r) <= MAP_RADIUS:
                hexes.append((q, r))
    return hexes

def get_base_positions():
    top_base = (0, -MAP_RADIUS)
    bottom_base = (0, MAP_RADIUS)
    return top_base, bottom_base