# Give a list of moves, compress them in order to move in parallel.
from copy import deepcopy


# This groups moves by if they could move together
# An improvement would be to smartly check if any move is compatible somehow


def is_compatible(group, other_move, storage):
    for move in group:
        # Don't allow the same box to move twice in one go
        if move.box_id == other_move.box_id:
            return False

    return storage.can_move_box(other_move.box_id, other_move.direction)[
        0
    ].__contains__("Successful")


def compress_moves(moves, storage):
    tempStorage = deepcopy(storage)
    groups = []
    current_group = []
    for move in moves:
        if is_compatible(current_group, move, tempStorage):
            current_group.append(move)
        else:
            groups.append(current_group)
            tempStorage.move_multiple_boxes(current_group)
            current_group = [move]

    groups.append(current_group)
    return groups
