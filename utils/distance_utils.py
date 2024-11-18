import math

def calculate_distance(pos1, pos2):
    return math.sqrt(sum((p1 - p2) ** 2 for p1, p2 in zip(pos1, pos2)))
