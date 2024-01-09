import random
from storage import (
    Position,
    Box,
    Storage,
    Direction,
)

# Random method functions


def random_check_box_existence(warehouse):
    warehouse.check_box_existence(get_random_box_id())


def random_check_position_in_bound(warehouse):
    warehouse.check_position_in_bound(get_random_box().position)


def random_add_box(warehouse):
    warehouse.add_box(get_random_box_id(), get_random_box())


def random_remove_box(warehouse):
    warehouse.remove_box(get_random_box_id())


def random_get_box_position(warehouse):
    warehouse.get_box_position(get_random_box_id())


def random_is_position_occupied(warehouse):
    warehouse.is_position_occupied(get_random_position())


def random_move_box(warehouse):
    warehouse.move_box(get_random_box_id(), get_random_direction())


def random_is_position_stable(warehouse):
    warehouse.is_position_stable(get_random_position())


# Helper Functions


def get_random_direction():
    directions = [
        Direction.North,
        Direction.South,
        Direction.Up,
        Direction.Down,
        Direction.East,
        Direction.West,
    ]
    return random.choice(directions)


def get_random_box_id():
    return large_random_number()


def get_random_box():
    return Box(get_random_position())


def get_random_position():
    return Position(large_random_number(), large_random_number(), small_random_number())


def large_random_number():
    return random.randint(0, 90)


def small_random_number():
    return random.randint(0, 2)


# stress testing

if __name__ == "__main__":
    warehouse = Storage(100, 100, 100)

    for i in range(0, 100000):
        print(random_check_box_existence(warehouse))
        print(random_check_position_in_bound(warehouse))
        print(random_add_box(warehouse))
        print(random_remove_box(warehouse))
        print(random_get_box_position(warehouse))
        print(random_is_position_occupied(warehouse))
        print(random_move_box(warehouse))
        print(random_is_position_stable(warehouse))
        print(warehouse.serialize_box_positions())
