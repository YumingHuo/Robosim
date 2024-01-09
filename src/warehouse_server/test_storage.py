from . import error_messages
from .storage import (
    Position,
    Box,
    Storage,
    Direction,
    movesDictionary,
)
from a_star_client.navigator import Move, swapOut, Node

Test_Box_id = 1


# Initialise a storage with one box in the middle
def single_box() -> Storage:
    storage_test = Storage(10, 10, 10)
    Test_box = Box(Position(5, 5, 0))
    storage_test.add_box(Test_Box_id, Test_box)
    return storage_test


# Initialise a storage for the special case of up
def single_box_up() -> Storage:
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(2, Box(Position(5, 5, 0)))
    storage_test.add_box(Test_Box_id, Box(Position(5, 4, 0)))
    return storage_test


# Initialise a storage for the special case of down
def single_box_down() -> Storage:
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(2, Box(Position(5, 5, 0)))

    storage_test.add_box(Test_Box_id, Box(Position(5, 5, 1)))

    # Make the storage unstable
    storage_test.move_box(Test_Box_id, Direction.North)
    return storage_test


# Construct a storage where the target box is completely sealed in, hence shouldn't be able to move at all
def blocked() -> Storage:
    storage_test = Storage(10, 10, 10)

    # Build the "base"
    storage_test.add_box(2, Box(Position(1, 1, 0)))
    storage_test.add_box(3, Box(Position(0, 1, 0)))
    storage_test.add_box(4, Box(Position(1, 0, 0)))
    storage_test.add_box(5, Box(Position(1, 2, 0)))
    storage_test.add_box(6, Box(Position(2, 1, 0)))

    # Add the test box
    storage_test.add_box(Test_Box_id, Box(Position(1, 1, 1)))

    # Fill in the "walls"
    storage_test.add_box(7, Box(Position(1, 2, 1)))
    storage_test.add_box(8, Box(Position(2, 1, 1)))
    storage_test.add_box(9, Box(Position(1, 0, 1)))
    storage_test.add_box(10, Box(Position(0, 1, 1)))

    # Add the top
    storage_test.add_box(11, Box(Position(1, 1, 2)))

    return storage_test


def out_bound_box(direction: Direction):
    # Mini storage to save tedious "column" building
    storage_test = Storage(2, 2, 2)
    if direction == direction.East:
        storage_test.add_box(42, Box(Position(1, 1, 0)))
        storage_test.add_box(Test_Box_id, Box(Position(1, 1, 1)))

    if direction == direction.West:
        storage_test.add_box(42, Box(Position(0, 1, 0)))
        storage_test.add_box(Test_Box_id, Box(Position(0, 1, 1)))

    if direction == direction.North:
        storage_test.add_box(42, Box(Position(1, 1, 0)))
        storage_test.add_box(Test_Box_id, Box(Position(1, 1, 1)))

    if direction == direction.South:
        storage_test.add_box(42, Box(Position(1, 0, 0)))
        storage_test.add_box(Test_Box_id, Box(Position(1, 0, 1)))

    if direction == direction.Up:
        storage_test.add_box(42, Box(Position(1, 1, 0)))
        storage_test.add_box(Test_Box_id, Box(Position(1, 1, 1)))

    if direction == direction.Down:
        storage_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    return storage_test


def test_opposite():
    assert Direction.North.opposite() == Direction.South
    assert Direction.South.opposite() == Direction.North
    assert Direction.East.opposite() == Direction.West
    assert Direction.West.opposite() == Direction.East
    assert Direction.Up.opposite() == Direction.Down
    assert Direction.Down.opposite() == Direction.Up


# Test adding a valid box to a valid position works
def test_add_box():
    storage_test = Storage(10, 10, 10)
    pos = Position(1, 3, 0)
    assert storage_test.is_valid_and_occupied(pos) is False
    storage_test.add_box(Test_Box_id, Box(pos))
    assert storage_test.get_box_position(Test_Box_id) == pos


# Test removing a valid box clears the position
def test_remove_box():
    storage_test = single_box()
    storage_test.remove_box(Test_Box_id)
    assert storage_test.is_valid_and_occupied(Position(5, 5, 0)) is False


# Test the limits of moving a box around in a direction
def assert_direction_tests(direction: Direction):
    storage_test = single_box()
    if direction == Direction.Down:
        storage_test_down = single_box_down()
        assert storage_test_down.move_box(
            Test_Box_id, Direction.Down
        ) == error_messages.MOVE_BOX.format(Test_Box_id)
    elif direction == Direction.Up:
        storage_test_up = single_box_up()
        assert storage_test_up.move_box(
            Test_Box_id, Direction.Up
        ) == error_messages.MOVE_BOX.format(Test_Box_id)
    else:
        assert storage_test.move_box(
            Test_Box_id, direction
        ) == error_messages.MOVE_BOX.format(Test_Box_id)

    storage_test = blocked()
    assert (
        storage_test.move_box(Test_Box_id, direction)
        == error_messages.BLOCKED_ERROR_MSG
    )

    storage_test = out_bound_box(direction)
    assert (
        storage_test.move_box(Test_Box_id, direction)
        == error_messages.OUT_OF_BOUNDS_ERROR_MSG
    )


# Test directions
def test_north():
    assert_direction_tests(Direction.North)


def test_east():
    assert_direction_tests(Direction.East)


def test_south():
    assert_direction_tests(Direction.South)


def test_west():
    assert_direction_tests(Direction.West)


def test_up():
    assert_direction_tests(Direction.Up)


def test_down():
    assert_direction_tests(Direction.Down)


# Make sure the box can only move up if it's being "supported" from the sides
def test_no_levitating_up():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    assert (
        storage_test.can_move_box(Test_Box_id, Direction.Up)[0]
        == error_messages.MOVE_BOX_UP_UNSUPPORTED_FROM_SIDES_ERROR_MSG
    )
    assert (
        storage_test.move_box(Test_Box_id, Direction.Up)
        == error_messages.MOVE_BOX_UP_UNSUPPORTED_FROM_SIDES_ERROR_MSG
    )


# Make sure the box can't crash into the ceiling in a 1 high storage
def test_ceiling_works():
    storage_test = Storage(10, 10, 1)
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    storage_test.add_box(99, Box(Position(0, 1, 0)))

    # If the ceiling was higher, the box could move up, but IT CAN'T

    assert (
        storage_test.can_move_box(Test_Box_id, Direction.Up)[0]
        == error_messages.OUT_OF_BOUNDS_ERROR_MSG
    )


# Check direction conversion happens regardless of letter case, but catches invalid inputs
def test_direction_from_str():
    # Valid cases
    assert Direction.from_str("north") == Direction.North
    assert Direction.from_str("West") == Direction.West
    assert Direction.from_str("EaSt") == Direction.East
    assert Direction.from_str("sOUtH") == Direction.South

    # Invalid cases
    assert Direction.from_str("Eastee") is None
    assert Direction.from_str("Souuuth") is None
    assert Direction.from_str(" -_- ") is None
    assert Direction.from_str(" ^ ^ ") is None
    assert Direction.from_str("') or True;DROP *--") is None


# Test adding a box twice returns the appropriate error
def test_add_exist_box():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(Test_Box_id, Box(Position(1, 1, 0)))
    assert (
        storage_test.add_box(Test_Box_id, Box(Position(2, 1, 0)))
        == error_messages.ADD_AN_EXIST_BOX_ERROR_MSG
    )


# Test adding a box outside the storage returns the appropriate error
def test_add_out_bounds_box():
    storage_test = Storage(10, 10, 10)
    assert (
        storage_test.add_box(Test_Box_id, Box(Position(10, 10, 10)))
        == error_messages.ADD_BOX_OUT_OF_BOUND_ERROR_MSG
    )


# Test adding a box in the same position as an existing box returns the appropriate error
def test_an_unavailable_adding():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(Test_Box_id, Box(Position(1, 1, 0)))
    assert (
        storage_test.add_box(2, Box(Position(1, 1, 0)))
        == error_messages.ADD_TO_A_OCCUPIED_PLACE_ERROR_MSG
    )


# Test removing a box that doesn't exist returns the appropriate error
def test_wrong_remove():
    storage_test = Storage(10, 10, 10)
    assert (
        storage_test.remove_box(Test_Box_id)
        == error_messages.REMOVE_A_NOT_EXIST_BOX_ERROR_MSG
    )


# Test moving a box that doesn't exist returns the appropriate error
def test_move_nonexistence_box():
    storage_test = Storage(10, 10, 10)
    assert (
        storage_test.move_box(Test_Box_id, Direction.from_str("north"))
        == error_messages.MOVE_A_NOT_EXIST_BOX_ERROR_MSG
    )


# Test moving a box on the ground works
def test_move_ground_slide():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    assert storage_test.move_box(
        Test_Box_id, Direction.from_str("north")
    ) == error_messages.MOVE_BOX.format(Test_Box_id)


# Test attempting to query a position outside of storage bounds correctly works
def test_invalid_position_query():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    assert not storage_test.check_position_in_bound(Position(-1, 0, 0))
    assert not storage_test.check_position_in_bound(Position(0, -1, 0))
    assert not storage_test.check_position_in_bound(Position(0, 0, -1))
    assert not storage_test.check_position_in_bound(Position(42, 100, "Hi"))
    assert storage_test.is_valid_and_occupied(Position(0, 0, 0))
    assert not storage_test.is_valid_and_occupied(Position(1, 0, 0))


# Test moving a box onto a supported location works
def test_move_supported_slide():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(8055, Box(Position(0, 0, 0)))
    storage_test.add_box(834, Box(Position(0, 1, 0)))
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 1)))

    assert storage_test.move_box(
        Test_Box_id, Direction.from_str("north")
    ) == error_messages.MOVE_BOX.format(Test_Box_id)


# Test adding boxes in midair Minecraft style returns the appropriate error
def test_no_floating_addition():
    storage_test = Storage(10, 10, 10)
    assert (
        storage_test.add_box(Test_Box_id, Box(Position(1, 1, 5)))
        == error_messages.ADD_A_BOX_MIDAIR_ERROR_MSG
    )


# Test moving boxes into midair updates the unstable box variable
def test_updating_unstable_box():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(89, Box(Position(0, 0, 0)))
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 1)))
    storage_test.move_box(Test_Box_id, Direction.North)
    assert storage_test.unstableBoxID == Test_Box_id


# Test you can only move the unstable box
def test_forced_unstable_box_move():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(89, Box(Position(0, 0, 0)))
    storage_test.add_box(420, Box(Position(5, 5, 0)))
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 1)))

    # Create the unstable box
    storage_test.move_box(Test_Box_id, Direction.North)

    # Try and move box 420
    assert (
        storage_test.move_box(420, Direction.North)
        == error_messages.MOVE_PERSISTANT_UNSTABLE_BOX_ERROR_MSG
    )


# Test you move resolve the unstable box
def test_must_be_stablised():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(89, Box(Position(0, 0, 0)))
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 1)))

    # Create the unstable box
    storage_test.move_box(Test_Box_id, Direction.North)

    # Try and move the unstable box to another unstable position
    assert (
        storage_test.move_box(Test_Box_id, Direction.North)
        == error_messages.MOVE_UNSTABLE_BOX_STAYS_UNSTABLE_ERROR_MSG
    )


# Test moving boxes into midair updates the unstable box variable
def test_resolve_unstable_box():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(89, Box(Position(0, 0, 0)))
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 1)))

    # Create the unstable box
    storage_test.move_box(Test_Box_id, Direction.North)

    # Resolve the unstable box
    assert storage_test.move_box(
        Test_Box_id, Direction.South
    ) == error_messages.MOVE_BOX.format(Test_Box_id)


# Test resolving an unstable box the non-trivial way
def test_step_down():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(89, Box(Position(0, 0, 0)))
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 1)))

    # Create the unstable box
    storage_test.move_box(Test_Box_id, Direction.North)

    # Resolve the unstable box sensibly (it's gone down a level)
    assert storage_test.move_box(
        Test_Box_id, Direction.Down
    ) == error_messages.MOVE_BOX.format(Test_Box_id)


# Test attempting to remove a box that is supporting another box returns the appropriate error
def test_this_is_not_Minecraft():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(89, Box(Position(0, 0, 0)))
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 1)))

    # Try and remove box 89
    assert (
        storage_test.remove_box(89)
        == error_messages.REMOVE_BOX_CAUSES_FLOATING_ERROR_MSG
    )


# Test removing a box that is NOT supporting another box succeeds
def test_top_layer_removal():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(89, Box(Position(0, 0, 0)))
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 1)))

    # Try and remove the test box
    assert storage_test.remove_box(Test_Box_id) == error_messages.REMOVE_BOX.format(
        Test_Box_id
    )


# Test attempting to remove a box that is supporting another box returns the appropriate error
def test_moving_a_supporting_box():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    storage_test.add_box(89, Box(Position(0, 0, 1)))

    # Try and move the test box
    assert (
        storage_test.move_box(Test_Box_id, Direction.North)
        == error_messages.MOVE_SUPPORTING_BOX_CAUSES_FLOATING_ERROR_MSG
    )


# Test moving upwards correctly adds the box as unstable
def test_move_up_reports_unstable():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(89, Box(Position(5, 5, 0)))
    storage_test.add_box(Test_Box_id, Box(Position(5, 4, 0)))
    storage_test.move_box(Test_Box_id, Direction.Up)

    assert storage_test.unstableBoxID == Test_Box_id


def test_move_multiple_boxes_same_box_multiple_times():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(Test_Box_id, Box(Position(5, 5, 0)))

    assert (
        storage_test.move_multiple_boxes(
            [Move(Test_Box_id, Direction.North), Move(Test_Box_id, Direction.East)]
        )
        == error_messages.MOVE_MULTIPLE_BOXES_SAME_BOX_MULTIPLE_TIMES
    )


def test_move_multiple_boxes_non_simultaneous_moves():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(1, Box(Position(0, 0, 0)))
    storage_test.add_box(2, Box(Position(0, 1, 0)))

    error_index = 1
    assert (
        storage_test.move_multiple_boxes(
            [Move(2, Direction.North), Move(1, Direction.North)]
        )
        == f"Invalid Multiple Moves, Move {error_index} is Invalid with error message: {error_messages.BLOCKED_ERROR_MSG}"
    )


def test_move_multiple_boxes_correct():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(Test_Box_id, Box(Position(5, 5, 0)))
    storage_test.add_box(5, Box(Position(0, 0, 0)))

    assert (
        storage_test.move_multiple_boxes(
            [Move(Test_Box_id, Direction.North), Move(5, Direction.North)]
        )
        == error_messages.SUCCESS_MESSAGE
    )


# Test removing the unstable box resets the unstableBoxID value
def test_remove_unstable():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    storage_test.add_box(2, Box(Position(0, 1, 0)))

    storage_test.move_box(Test_Box_id, Direction.Up)

    storage_test.remove_box(Test_Box_id)

    assert storage_test.unstableBoxID is None


def compare_dicts(dict1, dict2):
    for key in dict1:
        assert key in dict2, (
            "Error, couldn't find " + str(key) + " in the second dictionary"
        )
        for v in dict1[key]:
            assert v in dict2[key], (
                "Error, couldn't find "
                + str(v)
                + " in the second dictionaries values for key "
                + str(key)
                + ": "
                + str(dict2[key])
            )
    for key in dict2:
        assert key in dict1, (
            "Error, couldn't find " + str(key) + " in the first dictionary"
        )
        for v in dict2[key]:
            assert v in dict1[key], (
                "Error, couldn't find "
                + str(v)
                + " in the first dictionaries values for key "
                + str(key)
                + ": "
                + str(dict1[key])
            )


# Test adding a box underneath the unstable box stablises it
def test_add_stablises():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    storage_test.add_box(2, Box(Position(0, 1, 0)))

    storage_test.move_box(Test_Box_id, Direction.Up)
    storage_test.add_box(4, Box(Position(0, 0, 0)))

    assert storage_test.unstableBoxID is None


# Test adding one box updates the available moves
def test_available_moves_adding_one():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(123456, Box(Position(0, 0, 0)))

    compare_dicts(
        storage_test.getAvailableMoves(),
        {Position(x=0, y=0, z=0): [Position(x=0, y=1, z=0), Position(x=1, y=0, z=0)]},
    )


# Test adding two boxes next to each other updates the available moves
def test_available_moves_adding_two():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(12345, Box(Position(0, 0, 0)))
    storage_test.add_box(23456, Box(Position(1, 0, 0)))

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            Position(x=1, y=0, z=0): [
                Position(x=1, y=1, z=0),
                Position(x=2, y=0, z=0),
                Position(x=1, y=0, z=1),
            ],
            Position(x=0, y=0, z=0): [
                Position(x=0, y=1, z=0),
                Position(x=0, y=0, z=1),
            ],
        },
    )


# Test removing a box empties availableMoves
def test_available_moves_remove_to_clear():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(1, Box(Position(0, 0, 0)))
    storage_test.remove_box(1)

    assert storage_test.getAvailableMoves() == {}


# Test adding then moving a box correctly assigns available moves
def test_available_moves_moving_one():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(1, Box(Position(0, 0, 0)))
    storage_test.move_box(1, Direction.North)

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            Position(x=0, y=1, z=0): [
                Position(x=1, y=1, z=0),
                Position(x=0, y=2, z=0),
                Position(x=0, y=0, z=0),
            ],
        },
    )


# Test adding boxes on-top of each other invalidates movement of the one on the bottom
def test_available_moves_stack():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(1, Box(Position(0, 0, 0)))
    storage_test.add_box(2, Box(Position(0, 0, 1)))

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            Position(x=0, y=0, z=1): [
                Position(x=0, y=1, z=1),
                Position(x=1, y=0, z=1),
            ],
        },
    )


# Test adding boxes on-top of each other, then removing the box ontop, restores movement for the box on the bottom
def test_available_moves_stack_and_remove():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(1, Box(Position(0, 0, 0)))
    storage_test.add_box(2, Box(Position(0, 0, 1)))

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            Position(x=0, y=0, z=1): [
                Position(x=0, y=1, z=1),
                Position(x=1, y=0, z=1),
            ],
        },
    )

    storage_test.remove_box(2)

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            Position(x=0, y=0, z=0): [
                Position(x=0, y=1, z=0),
                Position(x=1, y=0, z=0),
            ],
        },
    )


# Test moving between "pillars" of boxes correctly calculates availableMoves
def test_available_moves_pillar_moves():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(1, Box(Position(0, 0, 0)))
    storage_test.add_box(2, Box(Position(0, 0, 1)))
    storage_test.add_box(3, Box(Position(1, 1, 0)))

    storage_test.move_box(2, Direction.East)
    storage_test.move_box(2, Direction.North)

    assert storage_test.unstableBoxID is None

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            # Box 1
            Position(x=0, y=0, z=0): [
                Position(x=0, y=1, z=0),
                Position(x=1, y=0, z=0),
            ],
            # Box 2
            Position(x=1, y=1, z=1): [
                Position(x=2, y=1, z=1),
                Position(x=1, y=2, z=1),
                Position(x=1, y=0, z=1),
                Position(x=0, y=1, z=1),
            ],
        },
    )


# Test wobbling a box doesn't affect the availableMoves
def test_available_moves_wobbling_does_nothing():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(1, Box(Position(0, 1, 0)))
    storage_test.add_box(2, Box(Position(1, 0, 0)))
    storage_test.add_box(3, Box(Position(1, 0, 1)))

    storage_test.move_box(3, Direction.West)
    storage_test.move_box(3, Direction.East)

    assert storage_test.unstableBoxID is None

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            # Box 1
            Position(x=0, y=1, z=0): [
                Position(x=1, y=1, z=0),
                Position(x=0, y=2, z=0),
                Position(x=0, y=0, z=0),
            ],
            # Box 3
            Position(x=1, y=0, z=1): [
                Position(x=2, y=0, z=1),
                Position(x=1, y=1, z=1),
                Position(x=0, y=0, z=1),
            ],
        },
    )


# Test wobbling a box slightly differently doesn't affect the availableMoves
# More specifically, test wobbling box 3 doesn't "erase" box 1 moving to (0, 0, 1)
def test_available_moves_wobbling_still_does_nothing():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(4, Box(Position(0, 1, 0)))
    storage_test.add_box(1, Box(Position(0, 1, 1)))
    storage_test.add_box(2, Box(Position(1, 0, 0)))
    storage_test.add_box(3, Box(Position(1, 0, 1)))

    storage_test.move_box(3, Direction.West)

    assert storage_test.unstableBoxID == 3

    compare_dicts(
        storage_test.availableMoves.locked,
        {
            # Box 4
            Position(x=0, y=1, z=0): [
                Position(x=1, y=1, z=0),
                Position(x=0, y=2, z=0),
                Position(x=0, y=0, z=0),
            ],
        },
    )

    compare_dicts(
        storage_test.availableMoves.unlocked,
        {
            # Box 1
            Position(x=0, y=1, z=1): [
                Position(x=1, y=1, z=1),
                Position(x=0, y=2, z=1),
                # Box 3 is in this position now - Position(x=0, y=0, z=1),
                # New move, since it "could" climb up box 3 (if it weren't unstable)
                Position(x=0, y=1, z=2),
            ],
            # Box 2
            Position(x=1, y=0, z=0): [
                Position(x=2, y=0, z=0),
                Position(x=1, y=1, z=0),
                Position(x=0, y=0, z=0),
            ],
            # Box 3
            Position(x=0, y=0, z=1): [
                Position(x=0, y=0, z=0),
                Position(x=1, y=0, z=1),
            ],
        },
    )

    storage_test.move_box(3, Direction.East)

    assert storage_test.unstableBoxID is None

    compare_dicts(
        storage_test.availableMoves.locked,
        {
            # Box 2
            Position(x=1, y=0, z=0): [
                Position(x=2, y=0, z=0),
                Position(x=1, y=1, z=0),
                Position(x=0, y=0, z=0),
            ],
            # Box 4
            Position(x=0, y=1, z=0): [
                Position(x=1, y=1, z=0),
                Position(x=0, y=2, z=0),
                Position(x=0, y=0, z=0),
            ],
        },
    )

    compare_dicts(
        storage_test.availableMoves.unlocked,
        {
            # Box 1
            Position(x=0, y=1, z=1): [
                Position(x=1, y=1, z=1),
                Position(x=0, y=2, z=1),
                Position(x=0, y=0, z=1),
            ],
            # Box 3
            Position(x=1, y=0, z=1): [
                Position(x=0, y=0, z=1),
                Position(x=1, y=1, z=1),
                Position(x=2, y=0, z=1),
            ],
        },
    )


# Test querying getAvailableMoves() for an unstable box
def test_available_moves_unstable():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(1, Box(Position(4, 4, 0)))
    storage_test.add_box(2, Box(Position(4, 3, 0)))

    storage_test.move_box(2, Direction.Up)

    assert storage_test.unstableBoxID == 2

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            # Box 2
            Position(x=4, y=3, z=1): [
                Position(x=4, y=3, z=0),
                Position(x=4, y=4, z=1),
            ],
        },
    )

    storage_test.move_box(2, Direction.North)

    assert storage_test.unstableBoxID is None

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            # Box 2
            Position(x=4, y=4, z=1): [
                Position(x=5, y=4, z=1),
                Position(x=4, y=5, z=1),
                Position(x=4, y=3, z=1),
                Position(x=3, y=4, z=1),
            ],
        },
    )

    storage_test.move_box(2, Direction.North)

    assert storage_test.unstableBoxID == 2

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            # Box 2
            Position(x=4, y=5, z=1): [
                Position(x=4, y=5, z=0),
                Position(x=4, y=4, z=1),
            ],
        },
    )


# Test adding a box midair correctly returns available moves
def test_available_moves_add_in_midair():
    storage_test = Storage(10, 10, 10)
    storage_test.add_box(1, Box(Position(4, 4, 0)))
    storage_test.add_box(2, Box(Position(4, 3, 1)), force=True)

    assert storage_test.unstableBoxID == 2

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            # Box 2
            Position(x=4, y=3, z=1): [
                Position(x=4, y=3, z=0),
                Position(x=4, y=4, z=1),
            ],
        },
    )


# Test "juggling"
def test_available_moves_move_around():
    storage_test = Storage(4, 4, 4)
    storage_test.add_box(2, Box(Position(0, 2, 0)))
    storage_test.add_box(1, Box(Position(0, 1, 0)))

    storage_test.move_box(1, Direction.Up)
    storage_test.move_box(1, Direction.Down)
    storage_test.move_box(2, Direction.Up)
    storage_test.move_box(2, Direction.Down)

    storage_test.move_box(1, Direction.Up)

    assert storage_test.unstableBoxID == 1

    compare_dicts(
        storage_test.getAvailableMoves(),
        {
            # Box 1
            Position(x=0, y=1, z=1): [
                Position(x=0, y=1, z=0),
                Position(x=0, y=2, z=1),
            ],
        },
    )


# Test swapOut recognises "gutter clinger" moves - adding a box allows floating boxes to stabilise on them
# TODO Could be avoided by adding boxes bottom to top
def test_available_moves_oddly_specific():
    storage_test = Storage(4, 4, 4)
    storage_test.add_box(1, Box(Position(0, 0, 0)))
    storage_test.add_box(2, Box(Position(0, 1, 0)))

    md = movesDictionary()
    md.unlocked = {
        Position(x=0, y=1, z=1): [
            Position(x=0, y=2, z=1),
            Position(x=0, y=1, z=0),
        ],
        Position(x=0, y=2, z=0): [
            Position(x=0, y=1, z=0),
            Position(x=1, y=2, z=0),
            Position(x=0, y=3, z=0),
        ],
    }

    mdp = movesDictionary()
    mdp.unlocked = {
        Position(x=0, y=1, z=0): [
            Position(x=0, y=1, z=1),
            Position(x=1, y=1, z=0),
            Position(x=0, y=0, z=0),
        ],
        Position(x=0, y=2, z=0): [
            Position(x=0, y=2, z=1),
            Position(x=1, y=2, z=0),
            Position(x=0, y=3, z=0),
        ],
    }

    parentNode = Node(
        None,
        Move(1, Direction.North),
        None,
        {1: Position(0, 1, 0), 2: Position(0, 2, 0)},
        mdp,
    )
    node = Node(
        parentNode,
        Move(1, Direction.Up),
        1,
        {1: Position(0, 1, 1), 2: Position(0, 2, 0)},
        md,
    )

    storage, restorePoint = swapOut(storage_test, node)

    compare_dicts(
        storage.getAvailableMoves(),
        {
            # Box 1
            Position(x=0, y=1, z=1): [
                Position(x=0, y=1, z=0),
                Position(x=0, y=2, z=1),
            ],
        },
    )
