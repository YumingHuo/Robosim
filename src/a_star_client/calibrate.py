import time
from collections import deque
import random

from warehouse_server.warehouse import seed
from a_star_client import navigator
from warehouse_server.storage import Position, Box
from warehouse_server.warehouse import Warehouse
from warehouse_server import utils

positiveInfinity = 100000


def assess(warehouse_test, startPos, endPos, weights, timelimit):
    def function():
        return navigator.a_star_navigate(
            warehouse_test, 1, startPos, endPos, weights=weights
        )

    outcome = utils.beat_the_clock(function, (), timelimit)

    if type(outcome) != deque:
        return positiveInfinity
    else:
        return len(outcome)


def try_maze(weights, timelimit) -> Warehouse:
    size = 6

    warehouse_test = Warehouse(size, size, 6)

    stencil = [
        [0, 1, 0, 0, 0, 0],
        [0, 1, 0, 1, 1, 0],
        [0, 1, 0, 0, 1, 0],
        [0, 1, 1, 0, 1, 0],
        [0, 0, 0, 0, 1, 0],
        [1, 1, 1, 1, 1, 0],
    ]

    warehouse_test.stencilLayer(stencil, 2)

    warehouse_test.add_box(1, Box(Position(0, 0, 0)))

    return assess(
        warehouse_test, Position(0, 0, 0), Position(5, 5, 0), weights, timelimit
    )


def try_dash(weights, timelimit) -> Warehouse:
    warehouse_test = Warehouse(20, 20, 20)

    warehouse_test.add_box(1, Box(Position(0, 0, 0)))

    return assess(
        warehouse_test, Position(0, 0, 0), Position(19, 19, 0), weights, timelimit
    )


def try_sliding(weights, timelimit) -> Warehouse:
    warehouse_test = Warehouse(3, 3, 1)

    warehouse_test.fillAreaWithBoxes(Position(0, 0, 0), Position(2, 2, 0), 1)

    warehouse_test.remove_box(warehouse_test.get_id_at_position(Position(2, 2, 0)))

    return assess(
        warehouse_test, Position(0, 0, 0), Position(2, 2, 0), weights, timelimit
    )


def try_seaOfNothing(weights, timelimit) -> Warehouse:
    warehouse_test = Warehouse(10, 10, 3)

    warehouse_test.fillAreaWithBoxes(Position(0, 0, 0), Position(9, 9, 1), 2)

    warehouse_test.add_box(1, Box(Position(0, 0, 2)))

    return assess(
        warehouse_test, Position(0, 0, 2), Position(9, 9, 2), weights, timelimit
    )


def try_underTheExit(weights, timelimit) -> Warehouse:
    Test_Box_id = 1

    warehouse_test = Warehouse(6, 6, 6)

    warehouse_test.add_box(Test_Box_id, Box(Position(0, 0, 0)))
    warehouse_test.add_box(2, Box(Position(0, 1, 0)))

    return assess(
        warehouse_test, Position(0, 0, 0), Position(0, 0, 1), weights, timelimit
    )


# Checks the algorithm moves boxes out of the way, rather than just "escorting" them
def try_escort(weights, timelimit) -> int:
    warehouse_test = Warehouse(10, 10, 10)

    warehouse_test.add_box(1, Box(Position(0, 0, 0)))
    warehouse_test.add_box(2, Box(Position(1, 0, 0)))

    return assess(
        warehouse_test, Position(0, 0, 0), Position(1, 0, 0), weights, timelimit
    )


def try_shimmy(weights, timelimit) -> Warehouse:
    difficulty = 4

    warehouse_test = Warehouse(3, difficulty, 1)

    warehouse_test.fillAreaWithBoxes(
        Position(0, 2, 0), Position(2, difficulty - 1, 0), 2
    )

    warehouse_test.add_box(1, Box(Position(0, 0, 0)))

    return assess(
        warehouse_test,
        Position(0, 0, 0),
        Position(0, difficulty - 1, 0),
        weights,
        timelimit,
    )


# Generates pseudo-random flat Warehouses with random targets
def try_random_superflat(weights, timelimit, theSeed=9) -> Warehouse:
    random.seed(theSeed)

    width = 6
    depth = 6
    height = 1

    total = 0

    for i in range(0, 2):
        warehouse_test = seed(
            random.randrange(0, 1000), width, depth, height, heightLimit=0
        )

        startPos = warehouse_test.get_box_position(1)

        # Cap the end z-position at 0 or 1
        endPos = Position(
            random.randrange(0, width - 1), random.randrange(0, depth - 1), 0
        )

        total += assess(warehouse_test, startPos, endPos, weights, timelimit)

    return total


# Generates random flat (0-1 max height) Warehouses with random targets
def try_random(weights, timelimit, theSeed=11) -> Warehouse:
    random.seed(theSeed)

    width = 6
    depth = 6
    height = 6

    warehouse_test = seed(
        random.randrange(0, 1000), width, depth, height, heightLimit=1
    )

    startPos = warehouse_test.get_box_position(1)

    # Cap the end z-position at 0 or 1
    endPos = Position(random.randrange(0, width - 1), random.randrange(0, depth - 1), 0)

    return assess(warehouse_test, startPos, endPos, weights, timelimit)


def try_many_superflat(weights, limit):
    total = 0
    random.seed(1)
    for i in range(0, 4):
        total += try_random_superflat(weights, limit, random.randint(0, 1000))

    return total


def try_many_random(weights, limit):
    total = 0
    random.seed(1234)
    for i in range(0, 4):
        total += try_random(weights, limit, random.randint(0, 1000))

    return total


def performTests(weights, limit):
    suites = [
        try_escort,
        try_shimmy,
        try_maze,
        try_dash,
        try_sliding,
        # try_seaOfNothing,
        try_underTheExit,
        try_random_superflat,
        try_random,
        try_many_superflat,
        try_many_random,
    ]

    total = 0
    for suite in suites:
        total += suite(weights, limit)
    return total


def getAccurateTimeAndSteps(weights, totalLimit):
    start = time.time()
    # Run the algorithm multiple times to increase accuracy
    runs = 2
    limit = totalLimit / runs
    bestSteps = performTests(weights, limit)
    for i in range(0, runs - 1):
        performTests(weights, limit)
    return round(time.time() - start, 4), bestSteps


def performGeneration(
    bestWeights,
    bestTotalTime,
    bestSteps,
    visited,
    childrenPerGeneration=5,
    variationRange=0.75,
):
    children = []
    for i in range(childrenPerGeneration):
        varied_tuple = tuple(
            [
                abs(round(x + random.uniform(-variationRange, variationRange), 2))
                for x in bestWeights
            ]
        )

        # Ensure you're generating a new set of weights
        while varied_tuple in visited:
            varied_tuple = tuple(
                [
                    abs(round(x + random.uniform(-variationRange, variationRange), 2))
                    for x in bestWeights
                ]
            )
        children.append(varied_tuple)
        visited.add(varied_tuple)

    results = []
    for child in children:
        trialTime, trialSteps = getAccurateTimeAndSteps(child, bestTotalTime * 1.1)
        results.append((child, trialSteps, trialTime))

    # Check which child did best
    for result in results:
        trialWeights, trialSteps, trialTime = result
        if (
            trialSteps == bestSteps and trialTime < bestTotalTime
        ) or trialSteps < bestSteps:
            print("Found better weights %s" % str(trialWeights))
            bestWeights = trialWeights
            bestSteps = trialSteps
            bestTotalTime = trialTime

    return bestWeights, bestTotalTime, bestSteps, visited


def test_main():
    # distanceFromStart distanceToExitApproximate boxesMoved exitClogged targetUnsafe
    bestWeights = (0.18, 0.65, 0.41, 1.29, 2.81)

    bestTotalTime, bestSteps = getAccurateTimeAndSteps(bestWeights, 100)

    print(bestTotalTime)

    generation = 1
    maxGenerations = 5
    variationRange = 0.5
    alpha = 0.95
    visited = set()

    while True:
        print("Starting generation %s" % generation)
        generation += 1
        bestWeights, bestTotalTime, bestSteps, visited = performGeneration(
            bestWeights,
            bestTotalTime,
            bestSteps,
            visited,
            variationRange=variationRange,
        )

        # Slowly shrink the variation range
        variationRange *= alpha

        if generation >= maxGenerations:
            break

    print(bestWeights)
    print(bestSteps)
    print(bestTotalTime)
