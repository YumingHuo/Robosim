# Misc errors
SUCCESS_MESSAGE = "Successful Operation!"
ADD_BOX = "Successful! Box {} has been added [{},{},{}]"
REMOVE_BOX = "Successful! Box {} has been removed"
MOVE_BOX = "Successful! Box {} has been moved"
OUT_OF_BOUNDS_ERROR_MSG = "Invalid Move, outside of the storage bounds!"
BLOCKED_ERROR_MSG = "Invalid Move, another box is in the way!"
ADD_EXIT_OUT_OF_BOUNDS_ERROR_MSG = "Invalid exit - it must be in the storage!"
ADD_WORMHOLE_EXIT_ERROR_MSG = "Invalid exit - wormholes aren't stable!"
DIRTY_MATRIX_ERROR_MSG = "Invalid stencil adding - the warehouse must be empty!"
STENCIL_OVERFLOW_ERROR_MSG = "Invalid stencil adding - the stencil will overflow!"
ROUTING_FULL_VISITED_ERROR_MSG = (
    "Too many visited nodes! Something's probably gone wrong"
)
ROUTING_FULL_QUEUE_ERROR_MSG = (
    "Too many nodes in the queue! Something's probably gone wrong"
)

# Adding errors
ADD_AN_EXIST_BOX_ERROR_MSG = "Invalid Adding, this box has already been added"
ADD_TO_A_OCCUPIED_PLACE_ERROR_MSG = "Invalid Adding, this position is occupied"
ADD_BOX_OUT_OF_BOUND_ERROR_MSG = "Invalid Adding, the position is out of storage bounds"
ADD_A_BOX_MIDAIR_ERROR_MSG = "Invalid Adding, there's nothing underneath this box"
ADD_A_NON_POSITIVE_BOX_ID_ERROR_MSG = (
    "Invalid Adding, box ID's must be positive integers"
)

# Removal errors
REMOVE_A_NOT_EXIST_BOX_ERROR_MSG = "Invalid Removing, the box does not exist"
REMOVE_BOX_CAUSES_FLOATING_ERROR_MSG = (
    "Invalid Removing, that's not a Minecraft tree - other boxes are being "
    "supported by that! "
)
REMOVE_LEAVES_CLIMBER_FLOATING_ERROR_MSG = (
    "Invalid Removing, the unstable box is climbing up that!"
)

# Moving errors
MOVE_A_NOT_EXIST_BOX_ERROR_MSG = "Invalid Move, the box does not exist"
MOVE_PERSISTANT_UNSTABLE_BOX_ERROR_MSG = (
    "Invalid move, you must resolve the unstable box!"
)
MOVE_UNSTABLE_BOX_STAYS_UNSTABLE_ERROR_MSG = (
    "Invalid move, that box is still unstable! It must be stablised"
)
MOVE_BOX_UP_UNSUPPORTED_FROM_SIDES_ERROR_MSG = (
    "Invalid move, that box isn't supported from any side, so it cannot move up"
)
MOVE_SUPPORTING_BOX_CAUSES_FLOATING_ERROR_MSG = (
    "Invalid move, that box is supporting something, so you can't move it!"
)
MOVE_MULTIPLE_BOXES_SAME_BOX_MULTIPLE_TIMES = (
    "Invalid multiple moves, you can't move the same box multiple times simultaneously!"
)

"""
Cases that must be accounted for:
- Can boxes overhang on the side of other boxes?
- How many overhangs are allowed?
- What is the maximum number of boxes that can be supported by an overhang?
- Can boxes "cling" to the edges of other boxes?
(So can this happen)
---S
000-
- How many edges allow boxes to cling to them?
- Can boxes roll over 1-wide gaps?
- Can boxes cling onto the edges in a corner shape
- Can boxes climb up walls?
- How high a wall can a box climb?
- Can boxes be supported by other boxes that are clinging onto edges?
- Is there a maximum height of boxes that can be stacked?
- Can boxes that have clung onto an edge climb up?
(So in this example, can box S get to position E?)
---E
S-00
0-00

"""
