from flask import Flask, send_file, send_from_directory
from eventlet import listen, wsgi
import glob
import os

IMAGE_AGE_OFFSET = 3

app = Flask(__name__, static_url_path="/", static_folder="web_client/static")


@app.route("/")
def index():
    return send_file("web_client/static/index.html")


@app.route("/image")
def image():
    files = [os.path.basename(x) for x in glob.glob("src/web_client/static/images/*")]
    files.sort(key=lambda x: os.path.getctime("src/web_client/static/images/" + x))
    selected_file = files[-IMAGE_AGE_OFFSET]
    r = send_from_directory("web_client/static/images", selected_file)
    return r
    # except Exception:
    # return ("", http.HTTPStatus.NO_CONTENT)


if __name__ == "__main__":
    wsgi.server(listen(("", 80)), app, log_output=False)
