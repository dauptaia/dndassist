from typing import Tuple, List


def get_crown_pos(
    pos_in: Tuple[int, int], width: int, height: int, radius: int
) -> List[Tuple[int, int]]:
    """Return the list of position for each crown around a position"""

    def _is_valid(pos):
        if pos[0] < 0:
            return False
        if pos[0] > width-1:
            return False
        if pos[1] < 0:
            return False
        if pos[1] > height-1:
            return False
        return True

    crown = []
    for i in range(-radius+1, radius+1):
        crown.append((pos_in[0] + i, pos_in[1] + radius))
    for j in range(radius-1, -radius-1, -1):
        crown.append((pos_in[0] + radius, pos_in[1] + j))
    for i in range(radius-1, -radius-1, -1):
        crown.append((pos_in[0] + i, pos_in[1] - radius))
    for j in range(-radius+1, radius+1):
        crown.append((pos_in[0] - radius, pos_in[1] + j))

    return [pos for pos in crown if _is_valid(pos)]

