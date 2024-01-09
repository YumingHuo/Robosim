from subprocess import Popen
from time import sleep
import atexit
import glob
import os

print("Starting Warehouse Server!")
warehouse_server = Popen(["python", "src/socket_server.py"])
sleep(1)

print("Starting Panda Server!")
panda = Popen(["python", "src/panda.py"])
sleep(1)

print("Starting Web Server!")
web_server = Popen(["python", "src/web.py"])
sleep(1)


def exit():
    warehouse_server.terminate()
    panda.terminate()
    web_server.terminate()

    # Clean up image files
    for filename in glob.glob("src/web_client/static/images/*"):
        os.remove(filename)


atexit.register(exit)

web_server.wait()
panda.wait()
warehouse_server.wait()
