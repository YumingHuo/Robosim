from eventlet import listen, wsgi
import socketio
from warehouse_server.storage import Box, Direction, Position, Storage
from io import StringIO
import csv
from a_star_client.navigator import Move
import json

INVALID_DIRECTION_ERROR_MSG = "Invalid direction, must be one of North, Souch, East, West, Up, Down (case in-sensitive)"

users = {}

with open("./src/user.json", "r", encoding="utf-8") as f:
    users = json.load(f)

admin_users = {}

with open("./src/admin.json", "r", encoding="utf-8") as f1:
    admin_users = json.load(f1)

login_status = {}


def is_int(x):
    if x[0] in ("-", "+"):
        return x[1:].isdigit()
    return x.isdigit()


def main():
    sio = socketio.Server(async_mode="eventlet", cors_allowed_origins="*")

    storage = Storage(10, 10, 10)

    panda = None

    @sio.event
    def connect(sid, _, __):
        print(f"client connected: {sid}")

    @sio.event
    def disconnect(sid):
        sio.leave_room(sid, "updates")

        if "admin" in login_status and login_status["admin"] == sid:
            del login_status["admin"]
        if "ordinary" in login_status and login_status["ordinary"] == sid:
            del login_status["ordinary"]

        print(f"client {sid} has unsubscribed from updates!")
        print(f"client disconnected: {sid}")

    @sio.event
    def add_box(sid, data):
        response = storage.add_box(
            data["box_id"], Box(Position(data["x"], data["y"], data["z"]))
        )
        publish_updates()

        return response

    @sio.event
    def remove_box(_, box_id):
        response = storage.remove_box(box_id)
        publish_updates()

        return response

    @sio.event
    def move_box(_, data):
        direction = Direction.from_str(data["direction"])
        if direction is None:
            return INVALID_DIRECTION_ERROR_MSG

        response = storage.move_box(data["box_id"], direction)
        publish_updates()

        return response

    @sio.event
    def move_multiple_boxes(_, data):
        moves = []
        for item in data:
            direction = Direction.from_str(item[1])
            if direction is None:
                return INVALID_DIRECTION_ERROR_MSG
            moves.append(Move(item[0], direction))

        response = storage.move_multiple_boxes(moves)
        publish_updates()

        return response

    @sio.event
    def csv_upload(_, fileContents):
        nonlocal storage

        if len(storage.boxes) != 0:
            return "Invalid, cannot upload CSV while there are boxes still in the warehouse!"

        file = StringIO(fileContents)
        reader = csv.reader(file)
        for row in list(reader)[1:]:
            if is_int(row[0]) and is_int(row[1]) and is_int(row[2]) and is_int(row[3]):
                box_id = int(row[0])
                x = int(row[1])
                y = int(row[2])
                z = int(row[3])

                response = storage.add_box(box_id, Box(Position(x, y, z)))
                if "Successful" not in response:
                    storage.clear_storage()
                    return f"Invalid Error during CSV upload: {response}"
            else:
                return "Invalid CSV file format!"

        publish_updates()
        return "Successfully loaded Storage from CSV"

    @sio.event
    def set_camera_preset(_, preset):
        nonlocal panda
        return sio.call("set_camera_preset", preset, to=panda)

    @sio.event
    def subscribe_updates(sid):
        print(f"client {sid} has subscribed to updates!")
        sio.enter_room(sid, "updates")

    @sio.event
    def set_panda(sid):
        nonlocal panda
        print(f"client {sid} has become the panda instance!")
        panda = sid

    @sio.event
    def get_state(sid, _):
        return storage.serialize_box_positions()

    @sio.event
    def mode(_, mode_str):
        nonlocal panda
        return sio.call("mode", mode_str, to=panda)

    @sio.event
    def clear_all_boxes(_):
        response = storage.clear_storage()
        publish_updates()
        return response

    def publish_updates():
        boxes = storage.serialize_box_positions()

        sio.emit("state", boxes, room="updates")

    @sio.event
    def get_access(sid, data):
        username = data["username"]
        password = data["password"]

        if username in users and users[username] == password:
            if "admin" in login_status:
                return "Invalid action, admin is already logged in"
            elif "ordinary" in login_status:
                return 0
            else:
                login_status["ordinary"] = sid
                return 1

        if username in admin_users and admin_users[username] == password:
            if "ordinary" in login_status:
                sio.emit("kick_out_login", skip_sid=sid)
                del login_status["ordinary"]
            if "admin" in login_status:
                sio.emit("kick_out_login", skip_sid=sid)
                del login_status["admin"]

            login_status["admin"] = sid
            return 2

        return "Invalid username or password"

    @sio.event
    def release_access(sid):
        if "admin" in login_status and login_status["admin"] == sid:
            del login_status["admin"]
        if "ordinary" in login_status and login_status["ordinary"] == sid:
            del login_status["ordinary"]

    app = socketio.WSGIApp(sio)
    wsgi.server(listen(("", 4000)), app, log_output=False)


if __name__ == "__main__":
    main()
