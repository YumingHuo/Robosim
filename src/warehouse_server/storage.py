from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Dict
from . import error_messages


class Direction(Enum):
    # This is the (index, value) of a Direction
    # Everything else is 0
    North = (1, 1)
    South = (1, -1)
    East = (0, 1)
    West = (0, -1)
    Up = (2, 1)
    Down = (2, -1)

    @staticmethod
    def from_str(string: str):
        string = string.lower()
        if string == "north":
            return Direction.North
        elif string == "east":
            return Direction.East
        elif string == "south":
            return Direction.South
        elif string == "west":
            return Direction.West
        elif string == "up":
            return Direction.Up
        elif string == "down":
            return Direction.Down
        else:
            return None

    def to_str(self):
        if self == Direction.Down:
            return "down"
        if self == Direction.East:
            return "east"
        if self == Direction.North:
            return "north"
        if self == Direction.South:
            return "south"
        if self == Direction.West:
            return "west"
        if self == Direction.Up:
            return "up"
        else:
            return None

    @staticmethod
    def getAll():
        return [
            Direction.North,
            Direction.East,
            Direction.South,
            Direction.West,
            Direction.Up,
            Direction.Down,
        ]

    @staticmethod
    def getAllCardinal():
        return [
            Direction.North,
            Direction.East,
            Direction.South,
            Direction.West,
        ]

    @staticmethod
    def getAllNotDown():
        return [
            Direction.North,
            Direction.East,
            Direction.South,
            Direction.West,
            Direction.Up,
        ]

    def opposite(self):
        return Direction((self.value[0], self.value[1] * -1))


@dataclass
class Position:
    x: int
    y: int
    z: int

    def __add__(self, direction: Direction):
        if direction.value[0] == 0:
            return Position(self.x + direction.value[1], self.y, self.z)
        elif direction.value[0] == 1:
            return Position(self.x, self.y + direction.value[1], self.z)
        elif direction.value[0] == 2:
            return Position(self.x, self.y, self.z + direction.value[1])

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def toString(self):
        return "(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"


# This assumes the position and destination are reachable by exactly one direction
def directionUsed(position, destination):
    if position.x - destination.x in (-1, 1):
        return Direction((0, -1 if position.x > destination.x else 1))
    elif position.y - destination.y in (-1, 1):
        return Direction((1, -1 if position.y > destination.y else 1))
    elif position.z - destination.z in (-1, 1):
        return Direction((2, -1 if position.z > destination.z else 1))
    else:
        exit("%s and %s are not reachable by only one Direction")


@dataclass
class Box:
    position: Position

    def __hash__(self):
        return hash(self.position)


class movesDictionary:
    # Boxes that can't move due to another box being on-top of it
    locked: dict
    # Boxes that can move
    unlocked: dict

    def __init__(self, locked=None, unlocked=None):
        if unlocked is None:
            unlocked = dict()
        if locked is None:
            locked = dict()
        self.locked = locked
        self.unlocked = unlocked

    def is_locked(self, pos: Position):
        return pos in self.locked

    def removeEndPos(self, pos: Position):
        self.locked = {
            key: [v for v in value if v != pos] for key, value in self.locked.items()
        }
        self.unlocked = {
            key: [v for v in value if v != pos] for key, value in self.unlocked.items()
        }

    def update(self, startPos: Position, endPositions, isLocked):
        if isLocked:
            self.locked.update({startPos: endPositions})
        else:
            self.unlocked.update({startPos: endPositions})

    def addMove(self, startPos, endPos):
        if startPos in self.locked:
            self.locked[startPos].append(endPos)
        elif startPos in self.unlocked:
            self.unlocked[startPos].append(endPos)
        else:
            exit(
                "Attempted to add move starting in %s, but it's not in the dictionary"
                % startPos
            )

    def hasMoveset(self, startPos):
        return startPos in self.locked or startPos in self.unlocked

    def deleteMoveset(self, startPos):
        if startPos in self.locked:
            self.locked[startPos] = []
        elif startPos in self.unlocked:
            self.unlocked[startPos] = []
        else:
            exit(
                "Attempted to delete moveset for Position %s, but no moveset exists"
                % startPos
            )

    def deleteEntry(self, startPos):
        if startPos in self.locked:
            del self.locked[startPos]
        elif startPos in self.unlocked:
            del self.unlocked[startPos]
        else:
            exit(
                "Attempted to delete entry Position %s, but no entry exists" % startPos
            )

    def getDestinations(self, startPos):
        if startPos in self.locked:
            return self.locked[startPos]
        elif startPos in self.unlocked:
            return self.unlocked[startPos]
        else:
            exit(
                "Attempted to get destinations for Position %s, but no moveset exists"
                % startPos
            )

    def removeDestination(self, startPos, endPos):
        if startPos in self.locked:
            self.locked[startPos].remove(endPos)
        elif startPos in self.unlocked:
            self.unlocked[startPos].remove(endPos)
        else:
            exit(
                "Attempted to remove destination %s for Position %s, but no destination exists"
                % (endPos, startPos)
            )

    def transferToLocked(self, startPos):
        if startPos in self.unlocked:
            endPositions = self.unlocked[startPos].copy()
            del self.unlocked[startPos]
            self.locked.update({startPos: endPositions})
        else:
            exit(
                "Attempted to transfer %s to locked status, but no key exists in unlocked"
                % startPos
            )

    def transferToUnlocked(self, startPos):
        if startPos in self.locked:
            endPositions = self.locked[startPos].copy()
            del self.locked[startPos]
            self.unlocked.update({startPos: endPositions})
        else:
            exit(
                "Attempted to transfer %s to unlocked status, but no key exists in unlocked"
                % startPos
            )

    def __len__(self):
        return len(self.locked) + len(self.unlocked)

    def __deepcopy__(self, memodict=None):
        newLocked = {key: value.copy() for key, value in self.locked.items()}
        newUnlocked = {key: value.copy() for key, value in self.unlocked.items()}

        return movesDictionary(newLocked, newUnlocked)


class Storage:
    # Initialise the storage with its dimensions
    def __init__(self, width: int, depth: int, height: int) -> None:
        self.boxes: Dict[int, Box] = {}
        # Make the list an element larger than we want, so it won't return IndexError: list index out of range
        self.matrix = [
            [[0 for _ in range(height)] for _ in range(depth)] for _ in range(width)
        ]

        self.width = width
        self.depth = depth
        self.height = height

        # Keeps track of if a previous move created an unsupported box
        self.unstableBoxID = None

        self.exitPosition = None

        self.availableMoves = movesDictionary()

    # Check if a box exists
    def check_box_existence(self, box_id: int) -> bool:
        return box_id in self.boxes

    # Check the box is in the bounds of the storage
    def check_box_in_bound(self, newbox: Box) -> bool:
        return self.check_position_in_bound(newbox.position)

    # Check a specific position is in the bounds of the storage
    def check_position_in_bound(self, position: Position) -> bool:
        # Make sure to check it's not negative
        return (
            (0 <= position.x < self.width)
            and (0 <= position.y < self.depth)
            and (0 <= position.z < self.height)
        )

    def addChecks(self, boxid: int, newbox: Box) -> str:
        # Check the boxid is a positive integer
        if boxid < 1:
            return error_messages.ADD_A_NON_POSITIVE_BOX_ID_ERROR_MSG

        # Check if the position is in bounds
        if not self.check_box_in_bound(newbox):
            return error_messages.ADD_BOX_OUT_OF_BOUND_ERROR_MSG

        # Check if the box either already exists, or is being put in the same position as another one
        for box_id, box in self.boxes.items():
            if box_id == boxid:
                return error_messages.ADD_AN_EXIST_BOX_ERROR_MSG
            if box.position == newbox.position:
                return error_messages.ADD_TO_A_OCCUPIED_PLACE_ERROR_MSG

        # Check the box wouldn't be floating in midair
        if not self.is_position_stable(newbox.position):
            return error_messages.ADD_A_BOX_MIDAIR_ERROR_MSG

        return error_messages.SUCCESS_MESSAGE

    # Add a box to the simulation (if you can)
    def add_box(self, boxid: int, newbox: Box, force=False, ignoreMoves=False):
        # Allows you to force adding a box if you want to
        if not force:
            message = self.addChecks(boxid, newbox)
            if message != error_messages.SUCCESS_MESSAGE:
                return message

        # Make sure if you're forcing to correctly assign the unstable box
        else:
            if not self.is_position_stable(newbox.position):
                self.unstableBoxID = boxid

        # Assign the position to the box
        self.boxes[boxid] = newbox
        self.matrix[newbox.position.x][newbox.position.y][newbox.position.z] = boxid

        # Check if you're stabilizing the unstable box
        if (
            self.is_valid_and_occupied(newbox.position + Direction.Up)
            and self.get_id_at_position(newbox.position + Direction.Up)
            == self.unstableBoxID
        ):
            self.unstableBoxID = None

        if not ignoreMoves:
            self.recalculateAvailableMoves(0, boxid, newbox.position)

        return error_messages.ADD_BOX.format(
            boxid, newbox.position.x, newbox.position.y, newbox.position.z
        )

    def removeChecks(self, boxid: int):
        # Check the box does exist
        if not self.check_box_existence(boxid):
            return error_messages.REMOVE_A_NOT_EXIST_BOX_ERROR_MSG

        pos = self.get_box_position(boxid)

        # Check the box is NOT on the "top layer"
        if self.is_valid_and_occupied(pos + Direction.Up):
            return error_messages.REMOVE_BOX_CAUSES_FLOATING_ERROR_MSG

        # Check you're not deleting a box that an unstable box is "climbing"
        # 0 0 1 0            0 0 1 0
        # 0 2 0 0 --del 2--> 0 0 0 0 ?!? (Box is now floating without any support)
        # 0 3 0 0            0 3 0 0
        if self.unstableBoxID not in (None, boxid):
            checkHooks = [
                pos + Direction.Up + d
                for d in Direction.getAllCardinal()
                if self.check_position_in_bound((pos + Direction.Up) + d)
            ]

            # If the deleting box is supporting the unstable box
            if any(
                self.get_id_at_position(hook) == self.unstableBoxID
                for hook in checkHooks
            ):
                return error_messages.REMOVE_LEAVES_CLIMBER_FLOATING_ERROR_MSG

        return True

    # Delete a box to the simulation (if you can)
    def remove_box(self, boxid: int, force=False, ignoreMoves=False):
        if not force:
            message = self.removeChecks(boxid)
            if message is not True:
                return message

        pos = self.get_box_position(boxid)

        self.matrix[pos.x][pos.y][pos.z] = 0
        del self.boxes[boxid]

        # Check if you're deleting the unstable box
        if self.unstableBoxID == boxid:
            self.unstableBoxID = None

        if not ignoreMoves:
            self.recalculateAvailableMoves(1, boxid, pos)

        return error_messages.REMOVE_BOX.format(boxid)

    # Attempt to ascertain a box's position
    def get_box_position(self, box_id: int) -> Position:
        return self.boxes[box_id].position

    # Get the box_id at a specific position
    def get_id_at_position(self, position: Position):
        return self.matrix[position.x][position.y][position.z]

    # Check if a VALID position is occupied, assuming it exists
    def is_valid_position_occupied(self, position: Position) -> bool:
        return not self.get_id_at_position(position) == 0

    # Check specifically if there's a box at the position
    def is_valid_and_occupied(self, position: Position):
        return self.check_position_in_bound(
            position
        ) and self.is_valid_position_occupied(position)

    # Determines if a box CAN be moved a direction
    # If it can't, return an error and a llama
    def can_move_box(self, box_id: int, direction: Direction) -> (str, str):
        current_position = self.get_box_position(box_id)

        newUnstableBoxIDValue = self.unstableBoxID

        # Check the box exists
        if not self.check_box_existence(box_id):
            return error_messages.MOVE_A_NOT_EXIST_BOX_ERROR_MSG, "Llama"

        next_position = current_position + direction

        # Check you're not going out of bounds
        if not self.check_position_in_bound(next_position):
            return error_messages.OUT_OF_BOUNDS_ERROR_MSG, "Llama"

        # Check you're not "crashing" into another box
        if self.is_valid_position_occupied(next_position):
            return error_messages.BLOCKED_ERROR_MSG, "Llama"

        # Check the box is NOT supporting another box
        if self.is_valid_and_occupied(current_position + Direction.Up):
            return error_messages.MOVE_SUPPORTING_BOX_CAUSES_FLOATING_ERROR_MSG, "Llama"

        # If you're not moving the unstable box, you must! Return an error
        if self.unstableBoxID is not None and self.unstableBoxID != box_id:
            return error_messages.MOVE_PERSISTANT_UNSTABLE_BOX_ERROR_MSG, "Llama"

        elif self.unstableBoxID is not None:
            # If the move moves it to an unstable position
            if not self.is_position_stable(next_position, self.unstableBoxID):
                return (
                    error_messages.MOVE_UNSTABLE_BOX_STAYS_UNSTABLE_ERROR_MSG,
                    "Llama",
                )
            # If you're moving to a stable position, that's fine
            else:
                newUnstableBoxIDValue = None

        # Edge case!
        # To avoid the box thinking it can support itself when moving up
        # Only allow it to do so if there's support from the sides (so it can "cling" to the edge)
        if direction == Direction.Up:
            if not (
                any(
                    self.is_valid_and_occupied(current_position + d)
                    for d in Direction.getAllCardinal()
                )
            ):
                return (
                    error_messages.MOVE_BOX_UP_UNSUPPORTED_FROM_SIDES_ERROR_MSG,
                    "Llama",
                )

            else:
                newUnstableBoxIDValue = box_id
        else:
            # Check you wouldn't be floating
            if not self.is_position_stable(next_position):
                # The move is legal, but the box is counted as unstable, and must be resolved on the next move
                newUnstableBoxIDValue = box_id

        return error_messages.SUCCESS_MESSAGE, newUnstableBoxIDValue

    def move_multiple_boxes(self, moves):
        # Check the same box doesn't have multiple moves
        seen_box_ids = set()
        for move in moves:
            if move.box_id in seen_box_ids:
                return error_messages.MOVE_MULTIPLE_BOXES_SAME_BOX_MULTIPLE_TIMES
            else:
                seen_box_ids.add(move.box_id)

        # Check all the moves can be done simultaneously and return
        # the first error otherwise
        for index, move in enumerate(moves):
            message = self.can_move_box(move.box_id, move.direction)[0]
            if message != error_messages.SUCCESS_MESSAGE:
                return f"Invalid Multiple Moves, Move {index} is Invalid with error message: {message}"

        # If the can all be done then do them
        for move in moves:
            self.move_box(move.box_id, move.direction)

        return error_messages.SUCCESS_MESSAGE

    # Move a box in a direction, if it's valid
    def move_box(self, box_id: int, direction: Direction, ignoreMoves=False):
        # Check the box exists
        if not self.check_box_existence(box_id):
            return error_messages.MOVE_A_NOT_EXIST_BOX_ERROR_MSG

        message, unstableBoxChange = self.can_move_box(box_id, direction)

        # If trying to move returns an error, return it!
        if message is not error_messages.SUCCESS_MESSAGE:
            return message

        current_position = self.get_box_position(box_id)
        next_position = current_position + direction

        # Remove the box from its current position
        self.matrix[current_position.x][current_position.y][current_position.z] = 0

        if self.unstableBoxID is not None:
            # Update the unstable box
            self.unstableBoxID = unstableBoxChange

        if not ignoreMoves:
            self.recalculateAvailableMoves(1, box_id, current_position)

        if self.unstableBoxID is None:
            # Update the unstable box
            self.unstableBoxID = unstableBoxChange

        # Add the box to its new position
        self.boxes[box_id].position = next_position
        self.matrix[next_position.x][next_position.y][next_position.z] = box_id

        if not ignoreMoves:
            self.recalculateAvailableMoves(0, box_id, next_position)

        return error_messages.MOVE_BOX.format(box_id)

    # Determines if the position in the storage has a box below it or is on the ground, hence stable
    def is_position_stable(self, position: Position, ignoreBox=None) -> bool:
        # Is it NOT on the ground?
        if position.z == 0:
            return True

        # Is there NOT a box below it
        positionBelow = position + Direction.Down
        if self.is_valid_and_occupied(positionBelow):
            if ignoreBox is None:
                return True
            else:
                if self.get_id_at_position(positionBelow) != ignoreBox:
                    return True

        return False

    def serialize_box_positions(self):
        boxes = []

        for box_id, box in self.boxes.items():
            boxes.append([box_id, box.position.x, box.position.y, box.position.z])

        return boxes

    def clear_storage(self):
        self.__init__(self.width, self.depth, self.height)
        return "All boxes have been cleared!"

    # Recalculate available moves based on the action performed, and returns the modified dictionary
    # "add" 0 - boxID, Position
    # "remove" 1 - boxID, Position
    def reassessAvailableMoves(
        self,
        action: int,
        boxID: int,
        posAttribute: Position,
        movesDict: movesDictionary,
    ):
        # Add
        if action == 0:
            # Remove moves that end in the box's position
            movesDict.removeEndPos(posAttribute)

            # If you're adding the box in midair, it's unstable!
            # Only used in navigator!
            if not self.is_position_stable(posAttribute):
                self.unstableBoxID = boxID

            # Add destinations that the new box can move to
            goodDestinations = [
                posAttribute + d
                for d in Direction.getAll()
                if self.can_move_box(boxID, d)[1] != "Llama"
            ]
            # Check if the box is locked (is there a box above it)
            isLocked = self.check_position_in_bound(
                posAttribute + Direction.Up
            ) and self.is_valid_position_occupied(posAttribute + Direction.Up)
            movesDict.update(posAttribute, goodDestinations, isLocked)

            # Add moves if neighbours can "climb" up the added box
            climbingNeighbours = [
                (posAttribute + d, posAttribute + d + Direction.Up)
                for d in Direction.getAllCardinal()
                if self.is_valid_and_occupied(posAttribute + d)
                and self.check_position_in_bound(posAttribute + d + Direction.Up)
                and not self.is_valid_position_occupied(posAttribute + d + Direction.Up)
            ]
            for item in climbingNeighbours:
                movesDict.addMove(item[0], item[1])

            # Add moves that allow floating boxes to stabilize themselves on
            # Used in swapOut
            gutterClingers = [
                (posAttribute + Direction.Up + d, posAttribute + Direction.Up)
                for d in Direction.getAllNotDown()
                if self.is_valid_and_occupied(posAttribute + Direction.Up + d)
                and not self.is_position_stable(posAttribute + Direction.Up + d)
            ]
            for item in gutterClingers:
                movesDict.addMove(item[0], item[1])

            # If there's a box below, lock it down!
            if self.is_valid_and_occupied(posAttribute + Direction.Down):
                movesDict.transferToLocked(posAttribute + Direction.Down)

        # Remove
        elif action == 1:
            # Remove the deleted box's moves
            movesDict.deleteEntry(posAttribute)

            # TODO maybe use Direction.getAllNotDown()
            # Add destinations that other boxes can move to
            for d in Direction.getAll():
                checkPosition = posAttribute + d
                # Check the position is valid
                if self.is_valid_and_occupied(checkPosition):
                    # Completely update the moves for the box below
                    # Since it's now free to move
                    if d == Direction.Down:
                        """# Add destinations that the new box can move to
                        goodDestinations = [
                            checkPosition + g
                            for g in Direction.getAll()
                            if self.can_move_box(
                                self.get_id_at_position(checkPosition), g
                            )[1]
                            != "Llama"
                        ]
                        # Delete moves that the box below currently has
                        # TODO Is this deletion needed?
                        if movesDict.hasMoveset(checkPosition):
                            movesDict.deleteMoveset(checkPosition)
                        for destination in goodDestinations:
                            movesDict.addMove(checkPosition, destination)"""

                        # Unlock the box below!
                        movesDict.transferToUnlocked(checkPosition)

                    # If the box there can move into the position available
                    # TODO Pretty sure this can be simplified
                    if (
                        not self.can_move_box(
                            self.get_id_at_position(checkPosition), d.opposite()
                        )[1]
                        == "Llama"
                    ):
                        movesDict.addMove(checkPosition, posAttribute)

            # Remove moves allowed by neighbours "climbing" the deleted box
            for d in Direction.getAllCardinal():
                nPosition = posAttribute + d
                # If the neighbouring box could climb up
                if (
                    self.is_valid_and_occupied(nPosition)
                    and self.check_position_in_bound(nPosition + Direction.Up)
                    and not self.is_valid_position_occupied(nPosition + Direction.Up)
                ):
                    # If it can't climb anymore
                    if not any(
                        self.is_valid_and_occupied(nPosition + look)
                        for look in Direction.getAllCardinal()
                    ):
                        # Remove it from the availableMoves dictionary (if it exists)
                        # This can occur if it's currently unstable
                        movesDict.removeDestination(nPosition, nPosition + Direction.Up)

        return movesDict

    # Recalculate available moves based on the action performed
    # "add" 0 - boxID, Position
    # "remove" 1 - boxID, Position
    def recalculateAvailableMoves(
        self, action: int, boxID: int, posAttribute: Position
    ):
        self.availableMoves = self.reassessAvailableMoves(
            action, boxID, posAttribute, self.availableMoves
        )

    def getAvailableMoves(self):
        if self.unstableBoxID is None:
            return self.availableMoves.unlocked

        else:
            unstablePosition = self.get_box_position(self.unstableBoxID)
            return {unstablePosition: self.availableMoves.unlocked[unstablePosition]}

    # Modifies an existing availableMoves dictionary with a move, and returns it
    def modifyMoves(self, dictionary, boxID: int, direction: Direction):
        # Save your own dictionary
        temp = self.availableMoves

        # Set the moves dictionary
        self.availableMoves = dictionary

        # Move the box
        self.move_box(boxID, direction)

        # Save the outcome
        returning = deepcopy(self.availableMoves)

        # Revert the changes
        self.move_box(boxID, direction.opposite())
        self.availableMoves = temp

        return returning

    def filterAllMoves(self, allMoves: dict):
        if self.unstableBoxID is None:
            # Only give moves for boxes that aren't supporting others
            filtered_dict = {}
            for position, destinations in allMoves.items():
                upPosition = position + Direction.Up
                if not self.check_position_in_bound(
                    upPosition
                ) or not self.is_valid_position_occupied(upPosition):
                    filtered_dict[position] = destinations
            return filtered_dict

        else:
            unstablePosition = self.get_box_position(self.unstableBoxID)
            return {
                unstablePosition: self.availableMoves.getDestinations(unstablePosition)
            }
