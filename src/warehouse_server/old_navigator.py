from dataclasses import dataclass
from typing import Dict

from storage import Direction, Position, Storage


# Construct a dictionary from a storage, setting every value in it to zero
def constructVisitedDictionary(storage: Storage):
    dictionary = Dict[Position, bool] = {}
    for w in storage.width:
        for d in storage.depth:
            for h in storage.height:
                dictionary.append(Position(w, d, h), False)
    return dictionary


# Note - storing the selectedBoxID here seems completely pointless, since you're only moving one box
# However, when this algorithm can move the other boxes, it's definitely needed
@dataclass
class Move:
    box_id: int
    direction: Direction


def breadthNavigateTo(
    storage: Storage,
    box_id: int,
    current_position: Position,
    target: Position,
    visited: Dict,
    route: [Move],
) -> []:
    # Have you arrived?
    if current_position == target:
        return route

    # Set the current position as visited
    visited.update({current_position: True})

    # Try all possible directions
    for direction in [
        Direction.North,
        Direction.East,
        Direction.South,
        Direction.West,
        Direction.Up,
        Direction.Down,
    ]:
        # Check the position is in bounds of the storage AND you haven't been there before
        next_position = current_position + direction
        if (storage.check_position_in_bound(next_position)) and (
            not visited[next_position]
        ):
            # Go there!
            route.append(Move(box_id, direction))
            breadthNavigateTo(storage, box_id, next_position, target, visited, route)

    # If you cannot move
    visited.update({current_position: False})

    return route
