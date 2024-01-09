import argparse
import time
from cli_client.connection import Connection
from warehouse_server.storage import Position, Storage, Box
from a_star_client.move_compression import compress_moves
from a_star_client.navigator import a_star_navigate

parser = argparse.ArgumentParser("A Star Algorithm")
parser.add_argument("--server", type=str, required=True)

parser.add_argument("box_id", type=int)
parser.add_argument("x", type=int)
parser.add_argument("y", type=int)
parser.add_argument("z", type=int)
parser.add_argument("--time", default=1, type=float)

args = parser.parse_args()
target = Position(args.x, args.y, args.z)

print("Connecting to server...")
conn = Connection(args.server)
state = conn.get_state()
print("Successfully connected to server: " + str(args.server))

print("Building Storage...")
storage = Storage(10, 10, 10)
for item in state:
    message = storage.add_box(
        item[0], Box(Position(item[1], item[2], item[3])), force=True
    )

    # Ensure nothing went wrong when constructing the Storage
    if not message.__contains__("Successful!"):
        print("Something went wrong when constructing the Storage!\n%s" % message)

print("Storage built successfully")

print("Finding route...")
route = a_star_navigate(
    storage,
    args.box_id,
    storage.get_box_position(args.box_id),
    target,
)

if type(route) == str:
    print("No route found:")
    print(route)
else:
    print("Found route!")
    groups = compress_moves(route, storage)
    for group in groups:
        print(group)
        time.sleep(args.time)
        formatted_group = []
        for move in group:
            formatted_group.append([move.box_id, move.direction.to_str()])
        conn.move_multiple_boxes(formatted_group)
conn.disconnect()
