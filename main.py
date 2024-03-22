from config import DATABASE_PATH
from database import Database, Profile
from flask import Flask, jsonify, request
from flask import render_template
from flask_socketio import SocketIO, send, emit, call

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
database = Database(DATABASE_PATH)
context = {}


@app.route("/")
def hello_world():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    print("Connected: {}".format(request.sid))


@socketio.on("disconnect")
def handle_disconnect():
    print("Disconnected: {}".format(request.sid))


def to_integer(text):
    if text == None:
        return None

    digits = "".join([ch for ch in text if ch >= "0" and ch <= "9"])

    if len(digits) == 0:
        return None

    return int(digits)


@socketio.on("initialize")
def handle_initialize(data):
    domain = data["domain"]

    if domain == "www.mamba.ru":
        # yapf: disable
        call("set", { "name": "name", "value": "div:has(> div[data-name=voting-photo]) div[data-name=item-title-name]" })
        call("set", { "name": "age", "value": "div:has(> div[data-name=voting-photo]) span[data-name=item-title-age]" })
        call("set", { "name": "photo", "value": "div[data-name=voting-photo] > img" })
        call("set", { "name": "prev", "value": "div[data-name=voting-photo] div[data-name=arrow-left]" })
        call("set", { "name": "next", "value": "div[data-name=voting-photo] div[data-name=arrow-right]" })
        call("set", { "name": "description", "value": "div:has(> div[data-name=voting-photo]) > div > div:has(div[data-name=item-title-name])" })
        call("set", { "name": "like", "value": "div[data-name=voting-photo] button[data-name=like-action]" })
        call("set", { "name": "dislike", "value": "div[data-name=voting-photo] button[data-name=dislike-action]" })
        call("autoskip", { "value": "div[data-name=notice-featured-rating] button:not([data-name=featured-photos-text])" })
        call("autoskip", { "value": "button[data-name=close-action]" })
        call("autoskip", { "value": "a[data-name=close-action]" })
        call("autowait", { "value": "div[data-name=uninotice-title-limit-voting]" })
        # yapf: enable
    else:
        raise Exception(
            "Connetion from unsupported domain `{}`.".format(domain))

    emit("start", {})


@socketio.on("recognize")
def handle_recognize(data):
    domain = data["domain"]
    autolike = data["autolike"]
    name = call("text", {"name": "name"})
    age = to_integer(call("text", {"name": "age"}))
    description = call("text", {"name": "description"})
    images = []

    while call("click", {"name": "prev"}):
        pass

    while True:
        image = call("attribute", {"name": "photo", "attribute": "src"})
        images.append(image)

        if not call("click", {"name": "next"}):
            break

    profile = Profile(domain, name, age, description, images)
    profile_id = database.save_profile(profile)
    context[request.sid] = profile_id

    call("message", {"message": "done"})


@socketio.on("like")
def handle_like(data):
    if request.sid in context:
        profile_id = context[request.sid]
        database.set_like(profile_id)

        call("click", {"name": "like"})
        call("message", {"message": "like"})
        emit("start", {})


@socketio.on("dislike")
def handle_dislike(data):
    if request.sid in context:
        profile_id = context[request.sid]
        database.set_dislike(profile_id)

        call("click", {"name": "dislike"})
        call("message", {"message": "dislike"})
        emit("start", {})


if __name__ == "__main__":
    app.static_folder = "static"
    socketio.run(app, debug=True)
