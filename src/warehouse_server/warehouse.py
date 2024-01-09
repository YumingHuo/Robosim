import random
import numpy as np
from itertools import chain

from .storage import Storage, Position, Box
from . import error_messages
from collections import deque


def getDimensions(data):
    dimensions = data[0]
    dimensionTuple = tuple(map(int, dimensions.split()))
    data = np.delete(data, 0)
    data = [[int(num) for num in line.split()] for line in data]
    return dimensionTuple, data


def formatData(data, dimensionTuple):
    formatted = data.reshape(dimensionTuple).tolist()
    return formatted


# Create a Storage from a seed
def seed(randSeed: int, width: int, depth: int, height: int, heightLimit=1):
    warehouse = Warehouse(width, depth, height)

    random.seed(randSeed)

    coordinates = deque([(i, j, 0) for i in range(width) for j in range(depth + 1)])

    currentBoxID = 1

    while len(coordinates) > 0:
        c = coordinates.popleft()

        # Pass if it's the first box
        if random.randint(0, 10) < 2 or currentBoxID == 1:
            pos = Position(c[0], c[1], c[2])
            warehouse.add_box(currentBoxID, Box(pos))
            currentBoxID += 1
            if c[2] + 1 < height and c[2] < heightLimit:
                coordinates.append((c[0], c[1], c[2] + 1))

    return warehouse


class Warehouse(Storage):
    # Add an exit to the warehouse
    def add_exit(self, exitPosition: Position):
        # Check the position is valid
        if not self.check_position_in_bound(exitPosition):
            return error_messages.ADD_EXIT_OUT_OF_BOUNDS_ERROR_MSG

        # Check the exit is exactly on the edge of the warehouse
        # Unless the warehouse has a wormhole in it, this is impossible
        if not (
            (exitPosition.x in (self.width - 1, 0))
            or (exitPosition.y in (self.depth - 1, 0))
            or (exitPosition.z in (self.height - 1, 0))
        ):
            return error_messages.ADD_WORMHOLE_EXIT_ERROR_MSG

        self.exitPosition = exitPosition

        return error_messages.SUCCESS_MESSAGE

    # Fills an area defined by two opposing corners with boxes
    # This is to save the inevitable amount of typing we'd have to do
    def fillAreaWithBoxes(
        self, startPosition: Position, endPosition: Position, firstID: int
    ):
        for x in range(startPosition.x, endPosition.x + 1):
            for y in range(startPosition.y, endPosition.y + 1):
                for z in range(startPosition.z, endPosition.z + 1):
                    self.add_box(firstID, Box(Position(x, y, z)))
                    firstID += 1

    def prettyPrintLayer(self, layer):
        # Find the largest element's character length
        maxLen = len(str(max(map(max, self.matrix))[0])) + 1

        for y in range(self.depth - 1, -1, -1):
            string = ""
            for x in range(0, self.width):
                # Add to the readout with a buffer
                value = str(self.matrix[x][y][layer])
                string = string + value + " " * (maxLen - len(value))
            print(string)

    # Draws a maze based on a 2D array
    def stencilLayer(self, stencil: [], startID: int):
        # Make sure the warehouse is empty
        if all(x == 0 for x in chain(self.matrix)):
            return error_messages.DIRTY_MATRIX_ERROR_MSG

        # Make sure the start coordinate doesn't overflow the stencil outside the warehouse
        if len(self.matrix) < len(stencil) or len(self.matrix[0]) < len(stencil[0]):
            return error_messages.STENCIL_OVERFLOW_ERROR_MSG

        for i in range(len(stencil)):
            for j in range(len(stencil[i])):
                if stencil[i][j] == 1:
                    self.add_box(startID, Box(Position(i, j, 0)))
                    startID += 1
