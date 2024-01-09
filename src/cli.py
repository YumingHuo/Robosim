import argparse

from connection import Connection


def add_box(conn, args):
    return conn.add_box(args.box_id, args.x, args.y, args.z)


def remove_box(conn, args):
    return conn.remove_box(args.box_id)


def move_box(conn, args):
    return conn.move_box(args.box_id, args.direction)


parser = argparse.ArgumentParser("RoboSim cli")
parser.add_argument("--server", type=str, required=True)

subparsers = parser.add_subparsers(required=True)

add_box_parser = subparsers.add_parser("add_box")
add_box_parser.add_argument("box_id", type=int)
add_box_parser.add_argument("x", type=int)
add_box_parser.add_argument("y", type=int)
add_box_parser.add_argument("z", type=int)
add_box_parser.set_defaults(func=add_box)

remove_box_parser = subparsers.add_parser("remove_box")
remove_box_parser.add_argument("box_id", type=int)
remove_box_parser.set_defaults(func=remove_box)

move_box_parser = subparsers.add_parser("move_box")
move_box_parser.add_argument("box_id", type=int)
move_box_parser.add_argument("direction", type=str)
move_box_parser.set_defaults(func=move_box)


args = parser.parse_args()

try:
    conn = Connection(args.server)
except Exception:
    print(f"No Server Running on {args.server}")
    quit()

print(args.func(conn, args))

conn.disconnect()
