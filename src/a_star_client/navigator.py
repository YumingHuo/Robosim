# Enable Node to include itself in the init method
from __future__ import annotations

from bisect import bisect_left
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from warehouse_server import error_messages
from warehouse_server.storage import (
    Direction,
    Position,
    Storage,
    Box,
    directionUsed,
    movesDictionary,
)
from warehouse_server.utils import noCrashing, boxChecks, noChanges

global safetyCheck
safeMode = False


@dataclass
class RestorePoint:
    movers: dict
    unstableBoxID: int
    availableMoves: dict

    def __init__(self, movers, unstableBoxID, availableMoves):
        self.movers = movers
        self.unstableBoxID = unstableBoxID
        self.availableMoves = availableMoves


@dataclass
class Move:
    box_id: int
    direction: Direction


class Node:
    def __init__(
        self,
        parentNode: Node,
        moveUsed: Move,
        unstableBoxID: int,
        movers: dict,
        availableMoves: movesDictionary,
    ):
        self.parentNode = parentNode
        self.moveUsed = moveUsed
        self.unstableBoxID = unstableBoxID

        self.distanceFromStart = 0
        self.distanceToExitApproximate = 0
        self.totalNumBoxesMoved = 0
        self.exitClogged = 0
        self.targetUnsafe = 0
        self.score = 0

        self.movers = movers
        self.totalBoxesMoved = set()

        self.availableMoves = availableMoves

    def boxCurrentPosition(self, box_id: int, storage: Storage) -> Position:
        if box_id in self.movers:
            return self.movers[box_id]
        else:
            return storage.get_box_position(box_id)

    def calculateScore(self, weights):
        self.score = (
            self.distanceFromStart * weights[0]
            + self.distanceToExitApproximate * weights[1]
            + self.totalNumBoxesMoved * weights[2]
            + self.exitClogged * weights[3]
            + self.targetUnsafe * weights[4]
        )

    def __hash__(self):
        return hash(frozenset(self.movers))

    def __eq__(self, other):
        return (
            self is not None
            and other is not None
            and self.movers.items() == other.movers.items()
        )

    # Allows nodes to be inserted in increasing order
    def __lt__(self, other):
        return self.score < other.score


def manhattanDistance(aPos: Position, bPos: Position):
    return abs(aPos.x - bPos.x) + abs(aPos.y - bPos.y) + abs(aPos.z - bPos.z)


def calculateUnsafe(
    neighbour: Node, target: Position, storage: Storage, selectedBoxID: int
):
    # Heavily penalise the target being unstable ON THE TARGET
    if storage.get_id_at_position(target) == selectedBoxID:
        neighbour.targetUnsafe += 20

    targetPos = target + Direction.Down

    # Look down from the target position
    while storage.check_position_in_bound(targetPos):
        boxID = storage.get_id_at_position(targetPos)
        # Penalise if there's not a stack supporting it
        if boxID == 0:
            neighbour.targetUnsafe += 4
        elif boxID is selectedBoxID:
            neighbour.targetUnsafe += 10
        else:
            # Otherwise, there's a supporting box, therefore you don't need to check the rest
            break

        targetPos += Direction.Down


def calculateClogged(
    neighbour: Node, target: Position, storage: Storage, selectedBoxID: int
):
    targetPos = target + Direction.Up

    # Look up from the target position
    while storage.check_position_in_bound(targetPos):
        boxID = storage.get_id_at_position(targetPos)
        # Penalise if there's not a stack supporting it
        if boxID is None:
            neighbour.targetUnsafe += 4
        elif boxID is selectedBoxID:
            neighbour.targetUnsafe += 10
        else:
            # Otherwise, there's a supporting box, therefore you don't need to check the rest
            break

        targetPos += Direction.Down


def swapOut(storage: Storage, node: Node):
    restorePoint = dict()
    restoreAvailableMoves = deepcopy(storage.availableMoves)
    restoreUnstableBoxID = storage.unstableBoxID

    # Check if it's the root
    if node.parentNode is None:
        return storage, RestorePoint(
            restorePoint, restoreUnstableBoxID, restoreAvailableMoves
        )

    # Remove all boxes which have moved in the PARENT NODE
    for box_id, position in node.parentNode.movers.items():
        # Store the box's current position
        originalPosition = storage.get_box_position(box_id)
        restorePoint.update({box_id: originalPosition})

        storage.remove_box(box_id, force=True, ignoreMoves=True)

    # Add the PARENT NODE boxes back in the correct positions
    for box_id, position in node.parentNode.movers.items():
        storage.add_box(box_id, Box(position), force=True, ignoreMoves=True)

    oldBoxPosition = storage.get_box_position(node.moveUsed.box_id)

    # Update the restorePoint with the new move IF the box wasn't in there
    if node.moveUsed.box_id not in restorePoint:
        restorePoint.update({node.moveUsed.box_id: oldBoxPosition})

    # Assign the available moves
    storage.availableMoves = storage.modifyMoves(
        node.parentNode.availableMoves, node.moveUsed.box_id, node.moveUsed.direction
    )

    # Apply the PARENT NODE unstable box
    storage.unstableBoxID = node.parentNode.unstableBoxID

    # Move the box!
    storage.move_box(node.moveUsed.box_id, node.moveUsed.direction, ignoreMoves=True)

    # Update the Node
    node.availableMoves = storage.availableMoves

    return storage, RestorePoint(
        restorePoint, restoreUnstableBoxID, restoreAvailableMoves
    )


def swapBack(storage: Storage, restorePoint: RestorePoint):
    storage.unstableBoxID = restorePoint.unstableBoxID

    for box_id, position in restorePoint.movers.items():
        storage.remove_box(box_id, force=True, ignoreMoves=True)

    for box_id, position in restorePoint.movers.items():
        storage.add_box(box_id, Box(position), force=True, ignoreMoves=True)

    storage.availableMoves = restorePoint.availableMoves

    return storage


def getPossibleNodes(
    storage: Storage,
    current_node: Node,
    onlyMoveThisBox: None or int,
    originalBoxPositions: dict,
):
    output = []

    for startPos, endPositions in storage.getAvailableMoves().items():
        # Ensure nothing's crashing into each other
        if safeMode:
            noCrashing(storage, startPos, endPositions)

        idOfBox = storage.get_id_at_position(startPos)
        if onlyMoveThisBox is not None and not idOfBox == onlyMoveThisBox:
            continue

        for endPos in endPositions:
            direction = directionUsed(startPos, endPos)

            # Don't bother adding the Node if you're just "reversing" the previous move
            if current_node.parentNode is not None:
                if current_node.parentNode.moveUsed.box_id == idOfBox:
                    if (
                        current_node.parentNode.moveUsed.direction.opposite()
                        == direction
                    ):
                        continue

            # Calculated when a Node is "opened"
            newAvailableMoves = None

            # Update the movers
            newMovers = dict(current_node.movers)

            # Check if the box has moved back to its original position
            # If so, remove it from the movers
            if originalBoxPositions[idOfBox].position == endPos:
                del newMovers[idOfBox]
            else:
                newMovers[idOfBox] = endPos

            # Calculate if the box is unstable
            if storage.is_position_stable(endPos, ignoreBox=idOfBox):
                unstable = None
            else:
                unstable = idOfBox

            newNode = Node(
                current_node,
                Move(idOfBox, direction),
                unstable,
                newMovers,
                newAvailableMoves,
            )

            output.append(newNode)

    return output


# Attempts to provide a series of moves that results in the target box reaching the exit
# This will fail (and return None) if the target box cannot reach the exit
def a_star_navigate(
    storage: Storage,
    selectedBoxID: int,
    start: Position,
    target: Position,
    onlyMoveThisBox=None,
    weights=(0.18, 0.65, 0.41, 1.29, 2.81),
) -> deque or None:
    # Check you're not already there
    if start == target:
        return deque()

    # Initialise things
    start_node = Node(None, Move(None, None), None, dict(), storage.availableMoves)
    start_node.distanceFromStart = 0
    start_node.distanceToExitApproximate = manhattanDistance(start, target)
    start_node.calculateScore(weights)

    queue = deque([start_node])

    visited = set()

    total = 0

    safe = deepcopy(storage)

    originalBoxPositions = deepcopy(storage.boxes)

    # Try and empty the queue
    while len(queue) > 0:
        # Pop the best node (the node at the start)
        current_node = queue.popleft()
        visited.add(current_node)

        # This is very useful when debugging!
        # print("\n%s. Currently inspecting %s" % (total, current_node.movers))
        total += 1

        # Temporarily limit nodes visited
        # Unless the storage is MASSIVE, visited is NEVER higher than this.
        if len(visited) > 50000:
            print(error_messages.ROUTING_FULL_VISITED_ERROR_MSG)
            return None

        if len(queue) > 50000:
            print(error_messages.ROUTING_FULL_QUEUE_ERROR_MSG)
            return None

        # Load the current node
        storage, restorePoint = swapOut(storage, current_node)

        # Perform some checks
        if safeMode:
            boxChecks(safe, storage)

        # Are you at the target?
        # And are you stable?
        if (
            current_node.distanceToExitApproximate == 0
            and current_node.unstableBoxID is None
        ):
            # Yay!
            # Trace back your steps
            path = deque()
            while current_node.parentNode is not None:
                path.append(current_node.moveUsed)
                current_node = current_node.parentNode
            path.reverse()

            # Repair the storage
            storage = swapBack(storage, restorePoint)

            return path

        if safeMode:
            safetyCheck = len(storage.availableMoves)

        neighbours = getPossibleNodes(
            storage, current_node, onlyMoveThisBox, originalBoxPositions
        )

        if safeMode:
            if safetyCheck != len(storage.availableMoves):
                exit(
                    "getPossibleNodes changed storage's available moves from %s to %s!"
                    % (safetyCheck, len(storage.availableMoves))
                )

        for neighbour in neighbours:
            # Ignore neighbours that have already been visited
            # The "any" operator is used, as it's marginally faster than the standard "in"
            # This is because it stops searching as soon as a match is found
            if any(visitedNode == neighbour for visitedNode in visited):
                continue

            # Assign the distanceFromStart value
            neighbour.distanceFromStart = current_node.distanceFromStart + 1

            # Find the first Node in the queue (from the back) that has a better/smaller distanceFromStart
            for i in range(len(queue) - 1, -1, -1):
                if queue[i].distanceFromStart < neighbour.distanceFromStart:
                    break
            else:
                i = -1

            # Search the sub-queue to check if there are any "better" Nodes in it than the neighbour
            for j in range(len(queue) - 1, i, -1):
                if queue[j] == neighbour:
                    if queue[j].distanceFromStart < neighbour.distanceFromStart:
                        continue

            current_position = neighbour.boxCurrentPosition(selectedBoxID, storage)

            # Assign the other values
            neighbour.distanceToExitApproximate = manhattanDistance(
                current_position, target
            )

            # Keep track of the total boxes moved and the total number of boxes moved
            neighbour.totalBoxesMoved = set(neighbour.parentNode.totalBoxesMoved)
            neighbour.totalNumBoxesMoved = neighbour.parentNode.totalNumBoxesMoved
            if neighbour.moveUsed.box_id not in neighbour.totalBoxesMoved:
                neighbour.totalBoxesMoved.add(neighbour.moveUsed.box_id)
                neighbour.totalNumBoxesMoved += 1

            neighbour.exitClogged = storage.is_valid_position_occupied(target)

            calculateUnsafe(neighbour, target, storage, selectedBoxID)

            neighbour.calculateScore(weights)

            # Add the child to the queue in the right place
            queue.insert(bisect_left(queue, neighbour), neighbour)

        storage = swapBack(storage, restorePoint)

        # Perform some checks
        if safeMode:
            noChanges(safe, storage)
