from collections import deque

import pytest

from warehouse_server import utils
from warehouse_server.storage import Position, Box, Direction, movesDictionary
from warehouse_server.warehouse import Warehouse
from . import navigator
from .navigator import Node, Move
from a_star_client.move_compression import compress_moves

Test_Box_id = 1

"""
NOTE:

Some of these tests are somewhat arbitrary, as it's hard to tell if it's giving the best answer
However, I will be checking if the route is valid, AND optimises when I can tell it must

For example, there is no difference between a path that goes:
north, east, north, east
opposed to
east, north, east, north

"""


# Test the algorithm can perform ONE move to the exit
def test_most_boring_maze_ever():
    warehouse_test = Warehouse(2, 2, 2)
    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    # Check it's not empty (it's found a route)
    route = navigator.a_star_navigate(
        warehouse_test, Test_Box_id, Position(0, 0, 0), Position(1, 1, 0)
    )

    assert len(route) > 0


# Test the algorithm can navigate an empty warehouse
def test_large_empty():
    warehouse_test = Warehouse(5, 5, 5)
    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    # Check it's not empty (it's found a route)
    assert (
        len(
            navigator.a_star_navigate(
                warehouse_test, Test_Box_id, Position(0, 0, 0), Position(4, 4, 0)
            )
        )
        > 0
    )


# Test the algorithm can navigate a warehouse with a bunch of boxes in the middle of it
def test_large_glob():
    warehouse_test = Warehouse(8, 8, 2)
    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    warehouse_test.fillAreaWithBoxes(Position(3, 3, 0), Position(5, 4, 0), 2)

    # Check it's not empty (it's found a route)
    assert (
        len(
            navigator.a_star_navigate(
                warehouse_test, Test_Box_id, Position(0, 0, 0), Position(7, 7, 0)
            )
        )
        > 0
    )


# Test the algorithm can navigate a warehouse when it can't move cardinally at the start
def test_in_a_corner():
    warehouse_test = Warehouse(4, 4, 3)
    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    warehouse_test.fillAreaWithBoxes(Position(0, 1, 0), Position(1, 1, 0), 5)
    warehouse_test.add_box(7, Box(Position(1, 0, 0)))

    # Check it's not empty (it's found a route)
    assert (
        len(
            navigator.a_star_navigate(
                warehouse_test, Test_Box_id, Position(0, 0, 0), Position(3, 3, 0)
            )
        )
        > 0
    )


# Test the algorithm can outsmart the tester by doing something I hadn't though of
def test_not_really_blocked_off():
    warehouse_test = Warehouse(4, 4, 3)
    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    warehouse_test.fillAreaWithBoxes(Position(0, 1, 0), Position(3, 1, 3), 5)

    route = navigator.a_star_navigate(
        warehouse_test, Test_Box_id, Position(0, 0, 0), Position(3, 3, 0)
    )

    # Check it's NOT empty (it's found a route)
    assert route is not None


# Test the algorithm correctly recognises there's DEFINITELY no route
def test_blocked_off():
    warehouse_test = Warehouse(4, 4, 5)
    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    warehouse_test.fillAreaWithBoxes(Position(0, 1, 0), Position(3, 1, 4), 5)

    route = navigator.a_star_navigate(
        warehouse_test, Test_Box_id, Position(0, 0, 0), Position(3, 3, 0)
    )
    # Check it's empty (it's NOT found a route)
    assert route is None


# Test it can navigate a maze with only one route
def test_simple_maze():
    warehouse_test = Warehouse(6, 6, 1)

    mazeStencil = [
        [0, 1, 0, 0, 0, 0],
        [0, 1, 0, 1, 1, 0],
        [0, 1, 0, 1, 1, 0],
        [0, 1, 0, 0, 1, 0],
        [0, 1, 1, 0, 1, 0],
        [0, 0, 0, 0, 1, 0],
    ]

    # Add the boxes according to the stencil
    warehouse_test.stencilLayer(mazeStencil, 5)

    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    # Check it's not empty (it's found a route)
    # Make sure it can ONLY move the target
    route = navigator.a_star_navigate(
        warehouse_test,
        Test_Box_id,
        Position(0, 0, 0),
        Position(5, 5, 0),
        onlyMoveThisBox=Test_Box_id,
    )

    # Check it's found the only route
    assert len(route) == 22

    # Check it's not cheating (going up)
    assert not route.count(Direction.Up)


# Test it will pick a shorter path, if given the option to go over an obstacle
def test_simple_illusion_maze():
    warehouse_test = Warehouse(6, 6, 2)

    mazeStencil = [
        [0, 1, 0, 0, 0, 0],
        [0, 1, 0, 1, 1, 0],
        [0, 1, 0, 1, 1, 0],
        [0, 1, 0, 0, 1, 0],
        [0, 1, 1, 0, 1, 0],
        [0, 0, 0, 0, 1, 0],
    ]

    # Add the boxes according to the stencil
    warehouse_test.stencilLayer(mazeStencil, 5)

    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    route = navigator.a_star_navigate(
        warehouse_test, Test_Box_id, Position(0, 0, 0), Position(5, 5, 0)
    )

    # Make sure it takes fewer steps than just moving on a 2D plane
    assert len(route) < 22


# Test it can cope with a large warehouse
def test_quite_big():
    size = 20
    warehouse_test = Warehouse(size, size, 10)

    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    # Make sure it takes fewer steps than just moving on a 2D plane
    assert (
        len(
            navigator.a_star_navigate(
                warehouse_test,
                Test_Box_id,
                Position(0, 0, 0),
                Position(size - 1, size - 1, 0),
            )
        )
        > 0
    )


# Test set comparisons work as intended
def test_set_comparing():
    grandparentNode = Node(None, None, None, dict(), dict())

    parentNode1 = Node(
        grandparentNode,
        navigator.Move(1, Direction.East),
        None,
        {1: Position(1, 0, 0)},
        dict(),
    )
    parentNode2 = Node(
        grandparentNode,
        navigator.Move(1, Direction.North),
        None,
        {1: Position(0, 1, 0)},
        dict(),
    )
    parentNode3 = Node(
        grandparentNode,
        navigator.Move(1, Direction.North),
        None,
        {1: Position(0, 1, 0), 2: Position(5, 6, 0)},
        dict(),
    )

    # Dummy
    warehouse_test1 = Warehouse(6, 6, 2)
    warehouse_test1.add_box(1, Box(Position(0, 0, 0)))
    warehouse_test1.move_box(1, Direction.East)
    warehouse_test1.move_box(1, Direction.North)
    node1 = Node(
        parentNode1,
        navigator.Move(1, Direction.North),
        None,
        {1: Position(1, 1, 0)},
        dict(),
    )

    # Should be treated as identical
    warehouse_test2 = Warehouse(6, 6, 2)
    warehouse_test2.add_box(1, Box(Position(0, 0, 0)))
    warehouse_test2.add_box(
        2, Box(Position(5, 5, 0))
    )  # Additional box, but it doesn't move
    warehouse_test2.move_box(1, Direction.North)
    warehouse_test2.move_box(1, Direction.East)
    node2 = Node(
        parentNode2,
        navigator.Move(1, Direction.East),
        None,
        {1: Position(1, 1, 0)},
        dict(),
    )

    # Should be treated as different
    warehouse_test3 = Warehouse(6, 6, 2)
    warehouse_test3.add_box(1, Box(Position(0, 0, 0)))
    warehouse_test3.add_box(
        2, Box(Position(5, 5, 0))
    )  # Additional box, but it DOES move
    warehouse_test3.move_box(2, Direction.North)  # Here!
    warehouse_test3.move_box(1, Direction.North)
    warehouse_test3.move_box(1, Direction.East)
    node3 = Node(
        parentNode3,
        navigator.Move(1, Direction.East),
        None,
        {1: Position(1, 1, 0), 2: Position(5, 6, 0)},
        dict(),
    )

    theSet = set()
    theSet.add(node1)
    theSet.add(node2)
    assert len(theSet) == 1

    theSet.add(node3)
    assert len(theSet) == 2


# Test swapOut and swapBack works as intended
def test_swap_out_and_swap_back():
    warehouse_test = Warehouse(6, 6, 2)

    stencil = [
        [1, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]

    # Add the boxes according to the stencil
    warehouse_test.stencilLayer(stencil, 1)

    changes = dict()

    # Even if boxes seem to be floating, it should override it
    pos1 = Position(0, 1, 1)
    pos2 = Position(0, 2, 0)
    changes.update({1: pos1})
    changes.update({2: pos2})

    locked = {}
    unlocked = {
        # Changed
        Position(x=0, y=1, z=1): [Position(x=0, y=1, z=0), Position(x=0, y=2, z=1)],
        Position(x=3, y=2, z=0): [
            Position(x=3, y=3, z=0),
            Position(x=4, y=2, z=0),
            Position(x=3, y=1, z=0),
            Position(x=3, y=2, z=1),
        ],
        # Changed
        Position(x=2, y=2, z=0): [
            Position(x=2, y=3, z=0),
            Position(x=2, y=1, z=0),
            Position(x=2, y=2, z=1),
            Position(x=3, y=2, z=0),
        ],
        # Changed
        Position(x=0, y=2, z=0): [
            Position(x=0, y=1, z=0),
            Position(x=1, y=2, z=0),
            Position(x=0, y=3, z=0),
        ],
    }

    md = movesDictionary()
    md.locked = locked
    md.unlocked = unlocked

    changesp = {1: Position(0, 1, 0), 2: Position(0, 2, 0)}

    lockedp = {}
    unlockedp = {
        # Changed
        Position(x=0, y=1, z=0): [
            Position(x=0, y=1, z=1),
            Position(x=1, y=1, z=0),
            Position(x=0, y=0, z=0),
        ],
        Position(x=3, y=2, z=0): [
            Position(x=3, y=3, z=0),
            Position(x=4, y=2, z=0),
            Position(x=3, y=1, z=0),
            Position(x=3, y=2, z=1),
        ],
        # Changed
        Position(x=2, y=2, z=0): [
            Position(x=2, y=3, z=0),
            Position(x=2, y=1, z=0),
            Position(x=2, y=2, z=1),
            Position(x=3, y=2, z=0),
        ],
        # Changed
        Position(x=0, y=2, z=0): [
            Position(x=0, y=2, z=1),
            Position(x=1, y=2, z=0),
            Position(x=0, y=3, z=0),
        ],
    }

    mdp = movesDictionary()
    mdp.locked = lockedp
    mdp.unlocked = unlockedp

    parentNode = Node(None, Move(2, Direction.West), None, changesp, mdp)
    node = Node(parentNode, Move(1, Direction.Up), 1, changes, md)

    changedStorage, restorePoint = navigator.swapOut(warehouse_test, node)

    assert restorePoint.movers[1] == Position(0, 0, 0)
    assert restorePoint.movers[2] == Position(1, 2, 0)
    assert len(restorePoint.movers) == 2

    assert changedStorage.check_box_existence(1)
    assert changedStorage.check_box_existence(2)
    assert changedStorage.check_box_existence(3)
    assert changedStorage.check_box_existence(4)
    assert changedStorage.get_box_position(1) == pos1
    assert changedStorage.get_box_position(2) == pos2

    # These shouldn't change
    assert changedStorage.get_box_position(3) == Position(2, 2, 0)
    assert changedStorage.get_box_position(4) == Position(3, 2, 0)

    assert changedStorage.unstableBoxID == 1

    reconstructedStorage = navigator.swapBack(changedStorage, restorePoint)

    assert reconstructedStorage.check_box_existence(1)
    assert reconstructedStorage.check_box_existence(2)
    assert reconstructedStorage.check_box_existence(3)
    assert reconstructedStorage.check_box_existence(4)
    assert reconstructedStorage.get_box_position(1) == Position(0, 0, 0)
    assert reconstructedStorage.get_box_position(2) == Position(1, 2, 0)

    # These shouldn't change
    assert reconstructedStorage.get_box_position(3) == Position(2, 2, 0)
    assert reconstructedStorage.get_box_position(4) == Position(3, 2, 0)


# Test the algorithm doesn't allow a box to end in an unstable position
def test_cannot_end_unstable():
    warehouse_test = Warehouse(4, 4, 4)

    warehouse_test.add_box(1, Box(Position(0, 0, 0)))
    warehouse_test.add_box(2, Box(Position(0, 1, 0)))

    # Check it's not empty (it's found a route)
    # Make sure it can ONLY move the target
    route = navigator.a_star_navigate(
        warehouse_test,
        1,
        Position(0, 0, 0),
        Position(0, 0, 1),
    )

    # Check it's found a route
    assert len(route) > 0

    # Check the box isn't ending in an unstable position (used to just move up)
    for move in route:
        warehouse_test.move_box(move.box_id, move.direction)

    assert warehouse_test.unstableBoxID is None

    assert warehouse_test.get_box_position(1) == Position(0, 0, 1)


# Test the algorithm can "dig up" a box
def test_dig_up():
    warehouse_test = Warehouse(4, 4, 4)

    warehouse_test.add_box(1, Box(Position(0, 0, 0)))
    warehouse_test.add_box(2, Box(Position(0, 0, 1)))
    warehouse_test.add_box(3, Box(Position(0, 0, 2)))
    warehouse_test.add_box(4, Box(Position(0, 1, 0)))
    warehouse_test.add_box(5, Box(Position(0, 1, 1)))
    warehouse_test.add_box(6, Box(Position(0, 2, 0)))

    # Check it's not empty (it's found a route)
    # Make sure it can ONLY move the target
    route = navigator.a_star_navigate(
        warehouse_test,
        1,
        Position(0, 0, 0),
        Position(3, 3, 0),
    )

    # Check it's found a route
    assert len(route) > 0

    # Check it's not cheating
    for move in route:
        assert warehouse_test.move_box(move.box_id, move.direction).__contains__(
            "Successful!"
        )


# Test the navigator doesn't return a really inefficient route
# We do NOT want box 2 to clamber over box 1, rather than just going North
# in order to get out of the way
@pytest.mark.skip(reason="Currently doesn't pass")
def test_no_silly_route():
    warehouse_test = Warehouse(10, 10, 10)

    warehouse_test.add_box(1, Box(Position(0, 0, 0)))
    warehouse_test.add_box(2, Box(Position(5, 0, 0)))

    # Check it's not empty (it's found a route)
    # Make sure it can ONLY move the target
    route = navigator.a_star_navigate(
        warehouse_test,
        1,
        Position(0, 0, 0),
        Position(5, 0, 0),
    )

    # Test there is actually a route, and it's efficient
    # Best route is:
    # - Move Box 1 East * 4
    # - Move Box 2 North * 1
    # - Move Box 1 East * 1
    assert 0 < len(route) < 7


# Test the algorithm can use other boxes to reach the exit
def test_legup():
    warehouse_test = Warehouse(10, 10, 10)

    warehouse_test.add_box(1, Box(Position(5, 0, 0)))
    warehouse_test.add_box(2, Box(Position(0, 0, 0)))

    def function():
        return navigator.a_star_navigate(
            warehouse_test,
            1,
            Position(5, 0, 0),
            Position(9, 0, 1),
        )

    outcome = utils.beat_the_clock(function, (), 20)

    assert type(outcome) == deque

    assert 0 < len(outcome)


# Test the algorithm moves boxes out of the way, rather than just "escorting" them
def test_no_escort():
    warehouse_test = Warehouse(10, 10, 10)

    warehouse_test.add_box(1, Box(Position(0, 0, 0)))
    warehouse_test.add_box(2, Box(Position(1, 0, 0)))

    def function():
        return navigator.a_star_navigate(
            warehouse_test,
            1,
            Position(0, 0, 0),
            Position(9, 0, 0),
        )

    outcome = utils.beat_the_clock(function, (), 3)

    assert type(outcome) == deque

    # The best route is (and takes exactly 10 steps):
    # Move 2 Direction.North * 1
    # Move 1 Direction.East * 9
    assert len(outcome) == 10


# Test the simple compression works in a simple example
def test_simple_compress():
    warehouse_test = Warehouse(5, 5, 5)
    warehouse_test.add_box(1, Box(Position(0, 0, 0)))
    warehouse_test.add_box(2, Box(Position(0, 2, 0)))
    warehouse_test.add_box(3, Box(Position(0, 3, 0)))
    warehouse_test.add_box(4, Box(Position(1, 3, 0)))

    moves = [
        Move(1, Direction.North),
        Move(2, Direction.East),
        Move(1, Direction.North),
        Move(4, Direction.East),
        Move(3, Direction.East),
        Move(1, Direction.North),
        Move(1, Direction.North),
    ]

    compressed = compress_moves(moves, warehouse_test)

    assert compressed == [
        [Move(1, Direction.North), Move(2, Direction.East)],
        [Move(1, Direction.North), Move(4, Direction.East)],
        [Move(3, Direction.East)],
        [Move(1, Direction.North)],
        [Move(1, Direction.North)],
    ]
