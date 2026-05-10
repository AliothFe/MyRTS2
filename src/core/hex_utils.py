import math
from src.core.constants import HEX_SIZE

def axial_to_pixel(q, r):
    x = HEX_SIZE * (math.sqrt(3) * q + math.sqrt(3)/2 * r)
    y = HEX_SIZE * (3/2 * r)
    return x, y

def pixel_to_axial(px, py):
    q = (math.sqrt(3)/3 * px - 1/3 * py) / HEX_SIZE
    r = (2/3 * py) / HEX_SIZE
    return axial_round(q, r)

def axial_round(q, r):
    s = -q - r
    rq = round(q)
    rr = round(r)
    rs = round(s)
    q_diff = abs(rq - q)
    r_diff = abs(rr - r)
    s_diff = abs(rs - s)
    if q_diff > r_diff and q_diff > s_diff:
        rq = -rr - rs
    elif r_diff > s_diff:
        rr = -rq - rs
    return rq, rr

def get_hex_corners(center_x, center_y, size=HEX_SIZE):
    corners = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.radians(angle_deg)
        corners.append(
            (center_x + size * math.cos(angle_rad),
             center_y + size * math.sin(angle_rad))
        )
    return corners