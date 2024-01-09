import socketio


class Connection:
    def __init__(self, url):
        self.sio = socketio.Client()
        self.sio.connect(url)

    def disconnect(self):
        self.sio.disconnect()

    def add_box(self, box_id, x, y, z):
        return self.sio.call("add_box", {"box_id": box_id, "x": x, "y": y, "z": z})

    def remove_box(self, box_id):
        return self.sio.call("remove_box", box_id)

    def move_box(self, box_id, direction: str):
        return self.sio.call(
            "move_box",
            {"box_id": box_id, "direction": direction},
        )

    def move_multiple_boxes(self, moves):
        return self.sio.call("move_multiple_boxes", moves)

    def get_state(self):
        return self.sio.call("get_state", "")
