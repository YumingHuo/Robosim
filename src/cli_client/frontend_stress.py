from connection import Connection
import random

test_directions = [
    "north",
    "nothr",
    "souch",
    "south",
    "wet",
    "west",
    "easta",
    "east",
    "NoRth",
    "WEst",
    "SoUTh",
    "EasT",
]


def random_small():
    return random.randint(0, 3)


def random_large():
    return random.randint(0, 18)


def random_massive():
    return random.randint(1, 1000)


conn = Connection("http://localhost:4000")

for i in range(100):
    print(
        conn.add_box(random_massive(), random_large(), random_large(), random_small())
    )
    print(conn.move_box(random.randint(1, 1000), random.choice(test_directions)))
    print(conn.remove_box(random_massive()))

print("\n\nRandom Requests Completed!\n")
conn.disconnect()
