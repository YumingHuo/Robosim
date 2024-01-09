import random
from . import error_messages
from .storage import Direction
from .storage import directionUsed
from .warehouse import seed
from .warehouse import Warehouse, Position, Box

Test_Box_id = 1


# Test adding an invalid exit returns the appropriate error, or succeeds
def test_wormhole_or_out_of_bounds_exit():
    warehouse_test = Warehouse(10, 10, 10)

    # Try and add an invalid exit
    assert (
        warehouse_test.add_exit(Position(1, 1, 1))
        == error_messages.ADD_WORMHOLE_EXIT_ERROR_MSG
    )
    assert (
        warehouse_test.add_exit(Position(15, 0, 0))
        == error_messages.ADD_EXIT_OUT_OF_BOUNDS_ERROR_MSG
    )
    assert warehouse_test.add_exit(Position(1, 0, 0)) == error_messages.SUCCESS_MESSAGE
    assert warehouse_test.add_exit(Position(1, 5, 0)) == error_messages.SUCCESS_MESSAGE
    assert warehouse_test.add_exit(Position(0, 6, 7)) == error_messages.SUCCESS_MESSAGE
    assert warehouse_test.add_exit(Position(0, 0, 9)) == error_messages.SUCCESS_MESSAGE


# Test filling in an area with boxes works as intended
def test_fill_command():
    warehouse_test = Warehouse(10, 10, 10)
    warehouse_test.fillAreaWithBoxes(Position(2, 3, 0), Position(4, 5, 0), 1)
    assert warehouse_test.is_valid_and_occupied(Position(2, 3, 0))
    assert warehouse_test.is_valid_and_occupied(Position(2, 4, 0))
    assert warehouse_test.is_valid_and_occupied(Position(2, 5, 0))
    assert warehouse_test.is_valid_and_occupied(Position(3, 3, 0))
    assert warehouse_test.is_valid_and_occupied(Position(3, 4, 0))
    assert warehouse_test.is_valid_and_occupied(Position(3, 5, 0))
    assert warehouse_test.is_valid_and_occupied(Position(4, 3, 0))
    assert warehouse_test.is_valid_and_occupied(Position(4, 4, 0))
    assert warehouse_test.is_valid_and_occupied(Position(4, 5, 0))

    assert not warehouse_test.is_valid_and_occupied(Position(2, 2, 0))
    assert not warehouse_test.is_valid_and_occupied(Position(2, 4, 1))
    assert not warehouse_test.is_valid_and_occupied(Position(4, 2, 0))


# Test compare function
def test_compare():
    storage_test = Warehouse(10, 10, 10)
    storage_test.fillAreaWithBoxes(Position(2, 3, 0), Position(4, 5, 1), 1)

    storage_test2 = Warehouse(10, 10, 10)
    storage_test2.fillAreaWithBoxes(Position(2, 3, 0), Position(4, 5, 1), 1)

    assert (
        storage_test.width == storage_test2.width
        and storage_test.depth == storage_test2.depth
        and storage_test.height == storage_test2.height
        and storage_test.unstableBoxID == storage_test2.unstableBoxID
        and str(storage_test.matrix) == str(storage_test2.matrix)
        and frozenset(storage_test.boxes.items())
        == frozenset(storage_test2.boxes.items())
    )


# Test there's no hovering shenanigans going on
# More specifically, a box "shimmying" up gaps
def test_no_hovering_shenanigins():
    warehouse_test = Warehouse(3, 3, 3)

    warehouse_test.fillAreaWithBoxes(Position(0, 0, 0), Position(2, 2, 1), 5)

    warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(1, 1, 1)))
    warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(1, 2, 1)))
    warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(2, 1, 1)))

    warehouse_test.add_box(Test_Box_id, Box(Position(1, 1, 1)))

    warehouse_test.move_box(22, Direction.West)
    warehouse_test.move_box(21, Direction.Up)
    assert not warehouse_test.move_box(21, Direction.Up).__contains__("Successful")


# Test seeding doesn't crash
def test_seed():
    warehouse = seed(42, 10, 10, 10)

    # Add pointless logic to remove warnings!
    uselessVariable = warehouse.unstableBoxID
    if uselessVariable == -1:
        pass


# Checks generated moves are correct!
def verify(warehouse: Warehouse):
    for startPos, endPosList in warehouse.getAvailableMoves().items():
        possibleDestinations = [
            startPos + direction for direction in Direction.getAll()
        ]
        for dest in possibleDestinations:
            message, unstable = warehouse.can_move_box(
                warehouse.get_id_at_position(startPos), directionUsed(startPos, dest)
            )

            if unstable == "Llama":
                assert dest not in endPosList, (
                    "An impossible move has been included "
                    + str(warehouse.get_id_at_position(startPos))
                    + ": "
                    + str(dest)
                )
            else:
                assert dest in endPosList, (
                    "A possible move has been excluded for box "
                    + str(warehouse.get_id_at_position(startPos))
                    + ": "
                    + str(dest)
                )


# Test available move generation is correct
def test_available_moves_add_only():
    warehouse = seed(420, 10, 10, 10)

    verify(warehouse)


def available_moves_add_and_move(theSeed: int, readout=False, intrigue=False):
    warehouse = seed(theSeed, 4, 4, 4)

    for i in range(0, 100):
        if readout:
            print("MOVE: " + str(i))

        # Check any moves are actually possible!
        if len(list(warehouse.getAvailableMoves().items())) == 0:
            if intrigue:
                print("No available moves! That isn't very likely!")
                warehouse.prettyPrintLayer(0)
                print("\n")
                warehouse.prettyPrintLayer(1)
                print("\n")
                warehouse.prettyPrintLayer(2)
            return

        randomBoxPosition, boxDestination = random.choice(
            list(warehouse.getAvailableMoves().items())
        )
        randomBoxDestination = random.choice(boxDestination)

        boxID = warehouse.get_id_at_position(randomBoxPosition)
        direction = directionUsed(randomBoxPosition, randomBoxDestination)

        if readout:
            print("**")
            warehouse.prettyPrintLayer(0)
            print("\n")
            warehouse.prettyPrintLayer(1)
            print("\n")
            warehouse.prettyPrintLayer(2)
            print("Unstable: " + str(warehouse.unstableBoxID))
            print(boxID)
            print(direction)

            warehouse.move_box(boxID, direction)
            print("**\n")

        verify(warehouse)


# Test available move generation is correct
def test_available_moves_add_and_move():
    # Add specific seeds you'd like to test here!
    seeds = [123, 456, 789, 1, 42, 9324, 34, 9039]

    # Add some random seeds!
    random.seed()
    for i in range(0, 20):
        seeds.append(random.randint(0, 10000))
    for s in seeds:
        available_moves_add_and_move(s)
