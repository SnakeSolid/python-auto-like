from config import DATABASE_PATH
from database import Database, Profile
from flask import Flask, jsonify, request
from flask import render_template
from flask_socketio import SocketIO, send, emit, call
from model import Model
from photo import analyze_photos

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
database = Database(DATABASE_PATH)
model = Model()
context = {}


def to_integer(text):
    if text == None:
        return None

    digits = "".join([ch for ch in text if ch >= "0" and ch <= "9"])

    if len(digits) == 0:
        return None

    return int(digits)


def analyze(profile_id):
    photos = database.select_profile_photos(profile_id)

    return analyze_photos(model, photos)


@app.route("/")
def hello_world():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    print("Connected: {}".format(request.sid))


@socketio.on("disconnect")
def handle_disconnect():
    print("Disconnected: {}".format(request.sid))


@socketio.on("initialize")
def handle_initialize(data):
    domain = data["domain"]

    if domain == "www.mamba.ru":
        # yapf: disable
        call("set", { "name": "name", "value": "div:has(> div[data-name=voting-photo]) div[data-name=item-title-name]" })
        call("set", { "name": "age", "value": "div:has(> div[data-name=voting-photo]) span[data-name=item-title-age]" })
        call("set", { "name": "description", "value": "div:has(> div[data-name=voting-photo]) > div > div:has(div[data-name=item-title-name])" })
        call("set", { "name": "prev", "value": "div[data-name=voting-photo] div[data-name=arrow-left]" })
        call("set", { "name": "next", "value": "div[data-name=voting-photo] div[data-name=arrow-right]" })
        call("set", { "name": "photo", "value": "div[data-name=voting-photo] > img" })
        call("set", { "name": "like", "value": "div[data-name=voting-photo] button[data-name=like-action]" })
        call("set", { "name": "dislike", "value": "div[data-name=voting-photo] button[data-name=dislike-action]" })
        call("autoskip", { "value": "div[data-name=notice-featured-rating] button:not([data-name=featured-photos-text])" })
        call("autoskip", { "value": "button[data-name=close-action]" })
        call("autoskip", { "value": "a[data-name=close-action]" })
        call("autowait", { "value": "div[data-name=uninotice-title-limit-voting]" })
        # yapf: enable
    elif domain == "prod-app7058363-5845152417b7.pages-ac.vk-apps.com":  # VK Dating
        # yapf: disable
        call("set", { "name": "name", "value": "div.UserFullInfo__main-header-name > div > span:nth-child(1)" })
        call("set", { "name": "age", "value": "div.UserFullInfo__main-header-name > div > span:nth-child(2)" })
        call("set", { "name": "description", "value": "div.UserFullInfo.UserFullInfo--vkcom" })
        call("set", { "name": "prev", "value": "div[data-testid=current-card] div[data-testid=prev-story-switcher]" })
        call("set", { "name": "next", "value": "div[data-testid=current-card] div[data-testid=next-story-switcher]" })
        call("set", { "name": "photos", "value": "div[data-testid=current-card] div > img" })
        call("set", { "name": "videos", "value": "div[data-testid=current-card] div > video > source" })
        call("set", { "name": "like", "value": "div[data-testid=current-card] div[role=button][data-testid=like]" })
        call("set", { "name": "dislike", "value": "div[data-testid=current-card] div[role=button][data-testid=dislike]" })
        call("autoskip", { "value": "div.CustomCardDesktopAside div.vkuiPlaceholder__action button.vkuiButton.vkuiButton--mode-tertiary" })
        call("autowait", { "value": "div.GetProductAbstractPanelDesktop" })
        # yapf: enable
    else:
        raise Exception(
            "Connection from unsupported domain `{}`.".format(domain))

    emit("start", {})


@socketio.on("recognize")
def handle_recognize(data):
    domain = data["domain"]

    emit("message", {"message": "parsing..."})

    name = call("text", {"name": "name"})
    age = to_integer(call("text", {"name": "age"}))
    description = call("text", {"name": "description"})

    if domain == "www.mamba.ru":
        photos = []

        while call("click", {"name": "prev"}):
            pass

        while True:
            photo = call("attribute", {"name": "photo", "attribute": "src"})
            photos.append(photo)

            if not call("click", {"name": "next"}):
                break

        profile = Profile(domain, name, age, description, photos)
    elif domain == "prod-app7058363-5845152417b7.pages-ac.vk-apps.com":  # VK Dating
        photos = [
            uri for uri in call("attributes", {
                "name": "photos",
                "attribute": "src"
            }) if uri is not None
        ]
        videos = [
            uri for uri in call("attributes", {
                "name": "videos",
                "attribute": "src"
            }) if uri is not None
        ]
        profile = Profile(domain, name, age, description, photos, videos)

    profile_id = database.save_profile(profile)
    context[request.sid] = profile_id

    emit("message", {"message": "analyzing..."})

    like_probability = analyze(profile_id)

    emit("prediction", {"value": like_probability})
    emit("message", {"message": "done"})


@socketio.on("like")
def handle_like(data):
    if request.sid in context:
        profile_id = context[request.sid]
        database.set_like(profile_id)

        call("click", {"name": "like"})
        emit("message", {"message": "like"})
        emit("start", {})


@socketio.on("dislike")
def handle_dislike(data):
    if request.sid in context:
        profile_id = context[request.sid]
        database.set_dislike(profile_id)

        call("click", {"name": "dislike"})
        emit("message", {"message": "dislike"})
        emit("start", {})


if __name__ == "__main__":
    app.static_folder = "static"
    socketio.run(app, debug=True)
