import os
import threading
from collections import deque
import socketio
from direct.gui.DirectGui import DirectLabel
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.MetaInterval import Sequence
from direct.showbase.ShowBase import ShowBase
from panda3d.core import LVecBase3f, ConfigVariableString

FPS = 2
NUM_BUFFER_IMAGES = 100

GENERAL_SCALE = 0.5


# Preset Camera Positions
camera_presets = {
    "front": (LVecBase3f(5, -15, 3), LVecBase3f(0, 0, 0)),
    "back": (LVecBase3f(5, 25, 3), LVecBase3f(180, 0, 0)),
    "top": (LVecBase3f(5, 5, 20), LVecBase3f(0, -90, 0)),
}


def CHANGED_PERSPECTIVE_MESSAGE(preset):
    return f"Camera has been changed to the {preset} perspective!"


class Panda(ShowBase):
    def __init__(self):
        display = ConfigVariableString("load-display")
        display.setValue("p3tinydisplay")

        ShowBase.__init__(self, windowType="offscreen")

        # set original color to light mode
        self.set_background_color(0.92, 0.92, 0.92)
        self.previous_boxes = set()
        self.box_models = {}  # a dictionary of box_id -> box_model

        self.set_camera_preset("front")

        # add the floor
        floor = self.loader.loadModel("web_client/floorPlaceholder.egg")
        floor.setPos(0, 0, 0)
        floor.set_scale(GENERAL_SCALE * 10)
        floor.reparentTo(self.render)

        # add the wall
        wall1 = self.loader.loadModel("web_client/wall.egg")
        wall1.setPos(0, 0, 0)
        wall1.setH(wall1, 90)
        wall1.set_scale(GENERAL_SCALE * 10)
        wall1.reparentTo(self.render)

        # wall on the right side
        wall2 = self.loader.loadModel("web_client/wall.egg")
        wall2.setPos(10, 0, 0)
        wall2.setH(wall2, 90)
        wall2.set_scale(GENERAL_SCALE * 10)
        wall2.reparentTo(self.render)

        # Start the screenshot loop
        sc = Func(self.special_screenshot)
        delay = Wait(1.0 / FPS)

        self.screenshot_sequence = Sequence(sc, delay)
        self.screenshot_sequence.loop()

        self.screenshot_deque = deque([])

    def set_camera_preset(self, preset):
        self.camera.setPosHpr(camera_presets[preset][0], camera_presets[preset][1])

    def positive_update_boxes(self, diff):
        for box in diff:
            box_model = self.loader.loadModel("web_client/box.egg")
            box_model.setScale(GENERAL_SCALE)
            box_model.setPos(box[1], box[2], box[3])
            label = DirectLabel(
                parent=box_model,
                text=str(box[0]),
                pos=(1, 0, 2.5),
                relief=None,
                text_fg=(0.3, 0.9, 0.01, 1),
            )
            label.setBillboardPointEye()
            box_model.reparentTo(self.render)
            self.box_models[box[0]] = box_model

    def negative_update_boxes(self, negative_diff):
        for box in negative_diff:
            self.box_models.pop(box[0]).removeNode()

    def update_state(self, new_boxes):
        for i in range(len(new_boxes)):
            new_boxes[i] = tuple(new_boxes[i])
        new_boxes_set = set(new_boxes)

        self.negative_update_boxes(self.previous_boxes.difference(new_boxes_set))
        self.positive_update_boxes(new_boxes_set.difference(self.previous_boxes))

        self.previous_boxes = new_boxes_set

    def special_screenshot(self):
        self.graphicsEngine.renderFrame()
        new_filename = self.screenshot("src/web_client/static/images/image")

        self.screenshot_deque.append(new_filename)

        if len(self.screenshot_deque) > NUM_BUFFER_IMAGES:
            os.remove(self.screenshot_deque.popleft())

    def color_mode(self, mode: str):
        if mode == "dark":
            self.set_background_color(0.11, 0.10, 0.09, 1.0)
        if mode == "light":
            self.set_background_color(0.92, 0.92, 0.92, 1.0)


def main():
    URL = "http://localhost:4000"
    sio = socketio.Client()

    lock = threading.Lock()

    panda = Panda()

    @sio.event
    def state(boxes):
        lock.acquire()
        panda.update_state(boxes)
        lock.release()

    @sio.event
    def set_camera_preset(preset):
        lock.acquire()
        panda.set_camera_preset(preset)
        lock.release()

        return CHANGED_PERSPECTIVE_MESSAGE(preset)

    @sio.event
    def mode(mode_str):
        lock.acquire()
        panda.color_mode(mode_str)
        lock.release()

    sio.connect(URL)
    sio.call("subscribe_updates")
    sio.call("set_panda")

    panda.run()


if __name__ == "__main__":
    main()
