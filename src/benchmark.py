import cProfile
import io
import pstats

from a_star_client import navigator
from warehouse_server import utils
from warehouse_server import warehouse
from warehouse_server.storage import Position, Box
from warehouse_server.warehouse import Warehouse


def benchmarkMaze() -> Warehouse:
    Test_Box_id = 1
    size = 6

    testWarehouse = Warehouse(size, size, 6)

    stencil = [
        [0, 1, 0, 0, 0, 0],
        [0, 1, 0, 1, 1, 0],
        [0, 1, 0, 0, 1, 0],
        [0, 1, 1, 0, 1, 0],
        [0, 0, 0, 0, 1, 0],
        [1, 1, 1, 1, 1, 0],
    ]

    testWarehouse.stencilLayer(stencil, 2)

    testWarehouse.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    return testWarehouse, Position(0, 0, 0), Position(5, 5, 0)


def benchmarkDash() -> Warehouse:
    Test_Box_id = 1

    testWarehouse = Warehouse(20, 20, 20)

    testWarehouse.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    return testWarehouse, Position(0, 0, 0), Position(19, 19, 0)


def benchmarkShimmy() -> Warehouse:
    Test_Box_id = 1

    difficulty = 4

    testWarehouse = Warehouse(3, difficulty, 1)

    testWarehouse.fillAreaWithBoxes(
        Position(0, 2, 0), Position(2, difficulty - 1, 0), 2
    )

    testWarehouse.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    return testWarehouse, Position(0, 0, 0), Position(0, difficulty - 1, 0)


def benchmarkSliding() -> Warehouse:
    testWarehouse = Warehouse(3, 3, 1)

    testWarehouse.fillAreaWithBoxes(Position(0, 0, 0), Position(2, 2, 0), 1)

    testWarehouse.remove_box(testWarehouse.get_id_at_position(Position(2, 2, 0)))

    return testWarehouse, Position(0, 0, 0), Position(2, 2, 0)


def benchmarkSeaOfNothing() -> Warehouse:
    Test_Box_id = 1

    testWarehouse = Warehouse(10, 10, 3)

    testWarehouse.fillAreaWithBoxes(Position(0, 0, 0), Position(9, 9, 1), 2)

    testWarehouse.add_box(Test_Box_id, Box(Position(0, 0, 2)))

    return testWarehouse, Position(0, 0, 2), Position(9, 9, 2)


def benchmarkUnderTheExit() -> Warehouse:
    Test_Box_id = 1

    testWarehouse = Warehouse(6, 6, 6)

    testWarehouse.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    testWarehouse.add_box(2, Box(Position(0, 1, 0)))

    return testWarehouse, Position(0, 0, 0), Position(0, 0, 1)


# Construct a Warehouse with incrementally more useless boxes lying around
def benchmarkMoreAndMore(strength) -> Warehouse:
    Test_Box_id = 1

    testWarehouse = Warehouse(11, 11, 11)

    testWarehouse.add_box(Test_Box_id, Box(Position(0, 0, 0)))

    xCount = 1
    yCount = 1
    zCount = 0
    for boxNumber in range(1, strength):
        if xCount > 10:
            xCount = 1
            yCount += 1
        if yCount > 10:
            xCount = 1
            yCount = 1
            zCount += 1
        if zCount > 10:
            print("Warehouse too small for this test. Running at strength=1100")
            break

        testWarehouse.add_box(boxNumber + 1, Box(Position(xCount, yCount, zCount)))
        xCount += 1

    return testWarehouse, Position(0, 0, 0), Position(10, 0, 0)


def benchmarkTestFunction(testWarehouse, Test_Box_id, startingPosition, endPosition):
    route = navigator.a_star_navigate(
        testWarehouse, Test_Box_id, startingPosition, endPosition
    )

    return route


# Initialise the storage outside the test
tests = [
    benchmarkMaze(),
    benchmarkDash(),
    benchmarkShimmy(),
    benchmarkSliding(),
    # benchmarkSeaOfNothing(),
    benchmarkUnderTheExit(),
    benchmarkMoreAndMore(2),
    # benchmarkMoreAndMore(1100),
]


def runSuites():
    testOutputs = []
    for storage, start, end in tests:
        print("Starting test")
        storage.__class__ = warehouse.Warehouse
        storage.prettyPrintLayer(0)
        testOutputs.append(benchmarkTestFunction(storage, 1, start, end))
        print("Test passed")
    return testOutputs


def runCleanSuites():
    for storage, start, end in tests:
        benchmarkTestFunction(storage, 1, start, end)


# Run the suites more than once to increase accuracy
thoroughness = "InvalidInput!"
import sys

args = sys.argv[1:]
if len(args) == 0:
    thoroughness = 0
elif len(args) == 1:
    try:
        thoroughness = int(args[0])
    except ValueError:
        exit("Invalid thoroughness value! It must be an integer!")
    if thoroughness < 0:
        exit("Invalid thoroughness value! It must be positive!")
else:
    exit("Too many arguments!")

pr = cProfile.Profile()
pr.enable()

outputs = runSuites()

for i in range(0, thoroughness - 1):
    print("Running check " + str(i + 1))
    runCleanSuites()

pr.disable()

# Make sure the test passed
if any(route is None for route in outputs):
    exit("Test failed - no route found!")
else:
    for route in outputs:
        utils.prettyPrintRoute(route)
        print("\n")

# stats = Stats(pr)
# stats.sort_stats("tottime").print_stats(10)

s = io.StringIO()
ps = pstats.Stats(pr, stream=s)
ps.sort_stats("tottime")
ps.print_stats(10)
ps.sort_stats("cumtime")
ps.print_stats(10)
output = s.getvalue()

# extract the time taken from the output
lines = output.strip().splitlines()
time_taken = float(lines[0].split()[-2])

print(output)
print("Time taken: %s" % time_taken)
if thoroughness != 0:
    print("Average Time: " + str(round(time_taken / thoroughness, 3)))
print("Move Score: %s" % sum([len(route) for route in outputs]))
print("Thoroughness: %s" % thoroughness)
