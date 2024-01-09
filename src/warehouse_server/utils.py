import ctypes
import pprint
import threading
from collections import deque
from itertools import groupby


# beat_the_clock(functionName, (a,b,...), limit)
def beat_the_clock(func, args, timeout):
    result = [None]
    exception = [None]

    def runWithArguments():
        try:
            result[0] = func(*args)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=runWithArguments)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        # The function has taken too long! Stop it!
        error = ctypes.py_object(Exception("Function exceeded allowed runtime"))
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), error
        )

        # Verifies the thread has been terminated
        if res == 0:
            return ValueError("Failed to raise exception in thread")

        return TimeoutError("Function exceeded allowed runtime")
    elif exception[0]:
        return exception[0]

    return result[0]


# Prints the route taken nicer
def prettyPrintRoute(route: deque):
    # Check you're actually given a deque, and NOT a None
    if route is None:
        return

    # Groups route by directions taken in a row
    nicerRoute = [list(j) for i, j in groupby(route)]

    for directionGroup in nicerRoute:
        print(
            "Move",
            directionGroup[0].box_id,
            directionGroup[0].direction,
            "* " + str(len(directionGroup)),
        )


def noDuplicates(storage, identifier):
    # Check no boxes have been duplicated in the matrix
    seen = set()
    # Check each element in the array
    for sublist1 in storage.matrix:
        for subsublist in sublist1:
            for elem in subsublist:
                # If the element has already been seen, something's gone wrong!
                if elem != 0 and elem in seen:
                    pprint.pprint(storage.matrix)
                    exit("Duplicated entry %s (%s)" % (elem, identifier))
                seen.add(elem)


def noCrashing(storage, startPos, endPositions):
    for e in endPositions:
        # Check if the end position is in an occupied space
        if storage.get_id_at_position(e) != 0:
            exit(
                "Error - a move would cause box %s at %s to crash into the box %s at %s"
                % (
                    storage.get_id_at_position(startPos),
                    startPos,
                    storage.get_id_at_position(e),
                    e,
                )
            )


def boxChecks(safe, storage):
    if safe.boxes.keys() != storage.boxes.keys():
        inSafeNotStorage = list(set(safe.boxes.keys()) - set(storage.boxes.keys()))
        inStorageNotSafe = list(set(safe.boxes.keys()) - set(storage.boxes.keys()))
        if len(inSafeNotStorage) != 0:
            exit("Boxes missing for storage: %s" % str(inSafeNotStorage))
        elif len(inStorageNotSafe) != 0:
            exit("Boxes missing for safe (somehow): %s" % str(inStorageNotSafe))
        else:
            print("Boxes appear to be missing, but I can't find anything!")


def noChanges(safe, storage):
    if safe.boxes != storage.boxes:
        pprint.pprint(safe.boxes)
        pprint.pprint(storage.boxes)
        exit("Box array not the same!")

    if safe.matrix != storage.matrix:
        exit("Matrix not the same!")

    if safe.unstableBoxID != storage.unstableBoxID:
        exit("UnstableID not the same!")

    if not all(
        set(safe.availableMoves.unlocked.get(key, []))
        == set(storage.availableMoves.unlocked.get(key, []))
        for key in set(safe.availableMoves.unlocked)
        | set(storage.availableMoves.unlocked)
    ):
        print("1")
        pprint.pprint(safe.availableMoves.unlocked)
        print("2")
        pprint.pprint(storage.availableMoves.unlocked)
        exit("Unlocked availableMoves not the same!")

    if not all(
        set(safe.availableMoves.locked.get(key, []))
        == set(storage.availableMoves.locked.get(key, []))
        for key in set(safe.availableMoves.locked) | set(storage.availableMoves.locked)
    ):
        print("1")
        pprint.pprint(safe.availableMoves.locked)
        print("2")
        pprint.pprint(storage.availableMoves.locked)
        exit("Locked availableMoves not the same!")
