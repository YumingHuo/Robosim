from collections import deque

import pytest

from . import navigator
from warehouse_server import utils
from warehouse_server.storage import Position, Box
from warehouse_server.warehouse import Warehouse

Test_Box_id = 1


# Test the navigator discards moves that cause boxes to "wobble"
# Essentially, become unstable, with the only resolving move to move back
# a.k.a. Completely pointless
def test_avoid_wobbling():
    size = 4
    warehouse_test = Warehouse(2 * size - 1, 2 * size - 1, 6)

    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    # Create "towers" with wobblable blocks at the top
    # The algorithm SHOULD dismiss these, so it should take barely any time
    otherID = 6
    for i in range(1, size):
        for j in range(1, size):
            warehouse_test.fillAreaWithBoxes(
                Position(2 * i - 1, 2 * j - 1, 0),
                Position(2 * i - 1, 2 * j - 1, 3),
                otherID,
            )
            otherID += 10

    def function():
        return navigator.a_star_navigate(
            warehouse_test,
            Test_Box_id,
            Position(0, 0, 0),
            Position(2 * size - 2, 2 * size - 2, 0),
        )

    outcome = utils.beat_the_clock(function, (), 3)

    assert type(outcome) == deque


def test_partial_rubiks_escape():
    warehouse_test = Warehouse(6, 6, 6)

    difficulty = 5

    warehouse_test.fillAreaWithBoxes(Position(0, 0, 0), Position(2, 2, 1), 5)
    warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(1, 1, 1)))
    warehouse_test.add_box(Test_Box_id, Box(Position(1, 1, 1)))

    if difficulty == 5:
        warehouse_test.fillAreaWithBoxes(Position(0, 0, 2), Position(2, 2, 2), 50)
        warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(2, 2, 2)))
        warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(2, 1, 2)))
        warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(1, 2, 2)))

    if difficulty < 4:
        warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(2, 2, 1)))
    if difficulty < 3:
        warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(2, 1, 1)))
    if difficulty < 2:
        warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(1, 2, 1)))

    def function():
        return navigator.a_star_navigate(
            warehouse_test, Test_Box_id, Position(1, 1, 1), Position(5, 5, 0)
        )

    warehouse_test.prettyPrintLayer(0)
    print("\n")
    warehouse_test.prettyPrintLayer(1)
    print("\n")
    warehouse_test.prettyPrintLayer(2)
    print("\n")

    outcome = utils.beat_the_clock(function, (), 10)

    assert type(outcome) == deque

    utils.prettyPrintRoute(outcome)


@pytest.mark.skip(
    reason="Currently takes too long, but should just need to add heuristic for if the target can move"
)
def test_full_open_rubiks_escape():
    warehouse_test = Warehouse(6, 6, 6)

    warehouse_test.fillAreaWithBoxes(Position(0, 0, 0), Position(2, 2, 2), 5)

    warehouse_test.remove_box(
        warehouse_test.get_id_at_position(Position(1, 1, 1)), force=True
    )

    warehouse_test.add_box(Test_Box_id, Box(Position(1, 1, 1)))

    def function():
        return navigator.a_star_navigate(
            warehouse_test, Test_Box_id, Position(1, 1, 1), Position(5, 5, 0)
        )

    outcome = utils.beat_the_clock(function, (), 10)

    assert type(outcome) == deque


def test_shimmy() -> Warehouse:
    difficulty = 4

    warehouse_test = Warehouse(3, difficulty, 1)

    warehouse_test.fillAreaWithBoxes(
        Position(0, 2, 0), Position(2, difficulty - 1, 0), 2
    )

    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    route = navigator.a_star_navigate(
        warehouse_test, Test_Box_id, Position(0, 0, 0), Position(0, difficulty - 1, 0)
    )

    assert type(route) == deque


def test_unstable_end() -> Warehouse:
    warehouse_test = Warehouse(4, 4, 4)

    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    warehouse_test.add_box(2, Box(Position(0, 1, 0)))

    route = navigator.a_star_navigate(
        warehouse_test, Test_Box_id, Position(0, 0, 0), Position(0, 0, 1)
    )

    assert type(route) == deque
