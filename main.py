from collections import namedtuple
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

AnalyzeResult = namedtuple("AnalyzeResult",
                           ["probability", "age", "gender", "race", "manual"])


def to_text(text):
    if text == None:
        return None

    index = text.rfind(",")

    if index == -1:
        return text

    return text[:index]


def to_integer(text):
    if text == None:
        return None

    digits = "".join([ch for ch in text if ch >= "0" and ch <= "9"])

    if len(digits) == 0:
        return None

    return int(digits)


def analyze(profile_id):
    photos = database.select_profile_photos(profile_id)
    marks = set()

    for (_, _, _, mark) in photos:
        marks.add(mark)

    if len(marks) == 1:
        mark = list(marks)[0]

        if mark == "like":
            return AnalyzeResult(1.0, None, None, None, True)
        elif mark == "dislike":
            return AnalyzeResult(0.0, None, None, None, True)

    result = analyze_photos(model, photos, database)

    return AnalyzeResult(result.probability, result.age, result.gender,
                         result.race, False)


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
        call("autoskip", { "value": "div[data-name=modal-dating-search] div:has(div > button) > a" })
        "div[data-name=modal-dating-search] div > a"
        call("autowait", { "value": "div[data-name=uninotice-title-limit-voting]" })
        # yapf: enable
    elif domain == "prod-app7058363-b9d08b274518.pages-ac.vk-apps.com":  # VK Dating
        # yapf: disable
        call("set", { "name": "name", "value": "div.vkuiCustomScrollView.vkuiCustomScrollView--hasPointer-none span.vkuiHeader__content-in > div > div > div > span:nth-child(1)" })
        call("set", { "name": "age", "value": "div.vkuiCustomScrollView.vkuiCustomScrollView--hasPointer-none span.vkuiHeader__content-in > div > div > div > span:nth-child(2)" })
        call("set", { "name": "description", "value": "div.vkuiCustomScrollView.vkuiCustomScrollView--hasPointer-none > div > div:has(section)" })
        call("set", { "name": "photos", "value": "div[data-testid=current-card] div > img" })
        call("set", { "name": "videos", "value": "div[data-testid=current-card] div > video > source" })
        call("set", { "name": "like", "value": "div[data-testid=current-card] div[role=button][data-testid=like]" })
        call("set", { "name": "dislike", "value": "div[data-testid=current-card] div[role=button][data-testid=dislike]" })
        call("autoskip", { "value": "div.CustomCardDesktopAside div.vkuiPlaceholder__action button.vkuiButton.vkuiButton--mode-tertiary" })
        call("autoskip", { "value": "div.vkuiPlaceholder button.vkuiButton.vkuiButton--mode-tertiary" })
        call("autoskip", { "value": "#match button.vkuiButton.vkuiButton--mode-secondary" })
        call("autowait", { "value": "div.GetProductAbstractPanelDesktop" })
        # yapf: enable
    elif domain == "teamo.date":
        # yapf: disable
        call("set", { "name": "name", "value": "div.user-name.faces-voter__name > span.user-name__text" })
        call("set", { "name": "age", "value": "div.user-name.faces-voter__name > span.user-name__text" })
        call("set", { "name": "description", "value": "div.profile-compatible__tab-content" })
        call("set", { "name": "photos", "value": "div.faces__photo__photos > img.faces__photo__photos__photo" })
        call("set", { "name": "like", "value": "div.faces-voter > span.faces-voter__button_yes" })
        call("set", { "name": "dislike", "value": "div.faces-voter > span.faces-voter__button_no" })
        call("autoskip", { "value": "div.popup-overlay.popup-overlay_visible > #newFrontendPopup > div.popup__close-button" })
        call("autowait", { "value": "div.faces > div.persons-pager__empty > div.button.button_green" })
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
    elif domain == "prod-app7058363-b9d08b274518.pages-ac.vk-apps.com":  # VK Dating
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
    elif domain == "teamo.date":
        photos = call("attributes", {"name": "photos", "attribute": "src"})
        profile = Profile(domain, to_text(name), age, description, photos)

    print("Name:", profile.name)
    print("Age:", profile.age)
    print("Description:", profile.description.replace("\n", " "))

    context[request.sid] = None
    profile_id = database.save_profile(profile)
    context[request.sid] = profile_id

    emit("message", {"message": "analyzing..."})

    result = analyze(profile_id)

    emit(
        "prediction", {
            "probability": result.probability,
            "age": result.age,
            "gender": result.gender,
            "race": result.race
        })

    if result.manual:
        if result.probability > 0.5:
            call("click", {"name": "like"})
            emit("message", {"message": "manual like"})
        else:
            call("click", {"name": "dislike"})
            emit("message", {"message": "manual dislike"})

        emit("start", {})
    else:
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
