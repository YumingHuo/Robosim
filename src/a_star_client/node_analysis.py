# Paste this code at the end of the getPossibleNodes() to compare it against the older method

"""

output2 = oldGetNodes(storage, onlyMoveThisBox, current_node)

movers1 = [node.movers for node in output1]
movers2 = [node.movers for node in output2]

allGood = True
for i in movers1:
    if i not in movers2:
        print("Couldn't find " + str(i) + " in movers2")
        allGood = False
for j in movers2:
    if j not in movers1:
        print("Couldn't find " + str(j) + " in movers1")
        allGood = False

if len(output1) != len(output2) or not allGood:
    print("\n")
    print("Oh no!")
    print(movers1)
    print([node.unstableBoxID for node in output1])

    print("\n")

    print(movers2)
    print([node.unstableBoxID for node in output2])
    storage.__class__ = Warehouse
    storage.prettyPrintLayer(0)
    print("\n")
    storage.prettyPrintLayer(1)
    print("\n")
    storage.prettyPrintLayer(2)
    print("\n")

    exit(0)"""


# And add this function in

"""

def oldGetNodes(
    storage: Storage, onlyMoveThisBox: None or int, current_node: Node
):
    output = []

    for box_id, box in storage.boxes.items():
        if onlyMoveThisBox is not None and not box_id == onlyMoveThisBox:
            continue

        if storage.unstableBoxID is not None and storage.unstableBoxID != box_id:
            continue

        for direction in Direction.getAll():
            message, unstable = storage.can_move_box(box_id, direction)

            # Catch cases where no other direction is possible
            if message in (
                error_messages.MOVE_PERSISTANT_UNSTABLE_BOX_ERROR_MSG,
                error_messages.MOVE_SUPPORTING_BOX_CAUSES_FLOATING_ERROR_MSG,
            ):
                break

            if message == error_messages.SUCCESS_MESSAGE:
                # Check you're not "wobbling" the box
                # if unstable == box_id and isWobbling(box_id, box, direction, storage):
                #    continue
                # Update the movers
                newMovers = current_node.movers.copy()
                newMovers.update({box_id: box.position + direction})
                newNode = Node(
                    current_node, Move(box_id, direction), unstable, newMovers
                )
                output.append(newNode)
    return output"""
