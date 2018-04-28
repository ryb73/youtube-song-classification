import rethinkdb as r
import jsoncfg
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import partial

config = jsoncfg.load_config(os.path.join(os.path.dirname(__file__), "config.json"))

app = Flask(__name__)
CORS(app)

def connect_db():
    return r.connect(host=config.rethinkdb.host(), port=config.rethinkdb.port(), db=config.rethinkdb.db())

@app.route("/get-tracks-to-process/", methods=["POST"])
def get_tracks_to_process():
    db = connect_db()
    req = request.get_json()

    track_type = req["trackType"]
    tracks = req["tracks"]

    searches = [ create_search(db, track_type, t) for t in tracks ]
    incomplete_searches = [ s for s in searches if not is_search_complete(db, s["id"]) ]

    return jsonify({
        "searches": incomplete_searches,
        "skipped": len(searches) - len(incomplete_searches)
    })

def create_search(db, track_type, track):
    query = get_query(track)

    print("q",query)
    print("t",track)
    id = get_track_by_type_id(db, track_type, track["id"])
    if id is not None:
        print("exists")
    else:
        print("doesn't exist, saving")
        doc = {
            "track": track,
            "trackType": track_type,
            "query": query
        }
        id = r.table("searches").insert(doc).run(db)["generated_keys"][0]

    return { "id": id, "query": query }

def is_search_complete(db, search_id):
    return r.table("selections").filter(r.row["searchId"] == search_id).contains().run(db)

def get_query(track):
    artists = [ a["name"] for a in track["artists"] ]
    return " ".join(artists) + " " + track["name"]

def get_track_by_type_id(db, type, id):
    res = list(r.table("searches").filter(r.row["trackType"] == type).filter(r.row["track"]["id"] == id).run(db))
    if len(res) < 1:
        return None
    return res[0]["id"]

@app.route("/save-youtube-channels/", methods=["POST"])
def save_youtube_channels():
    db = connect_db()
    req = request.get_json()

    r.table("youTubeChannels").insert(req["channels"]).run(db)
    return jsonify(True)

@app.route("/get-youtube-channels/", methods=["GET"])
def get_youtube_channels():
    db = connect_db()

    channel_ids = request.args.getlist("channelIds")
    matches = [ (id, get_channel(db, id)) for id in channel_ids ]

    return jsonify({
        "missingChannelIds": [ id for id, match in matches if match is None ],
        "matchingChannels": [ match for id, match in matches if match is not None ]
    })

def get_channel(db, id):
    return r.table("youTubeChannels").get(id).run(db)

@app.route("/save-videos/", methods=["POST"])
def save_videos():
    db = connect_db()
    req = request.get_json()

    r.table("videos").insert(req["videos"]).run(db)
    return jsonify(True)

@app.route("/get-videos/", methods=["GET"])
def get_videos():
    db = connect_db()

    video_ids = request.args.getlist("videoIds")
    matches = [ (id, get_video(db, id)) for id in video_ids ]

    return jsonify({
        "missingVideoIds": [ id for id, match in matches if match is None ],
        "matchingVideos": [ match for id, match in matches if match is not None ]
    })

def get_video(db, id):
    return r.table("videos").get(id).run(db)

@app.route("/get-match-types/", methods=["GET"])
def get_match_types():
    db = connect_db()

    return jsonify(list(r.table("matchTypes").run(db)))

@app.route("/add-match-types/", methods=["POST"])
def add_match_types():
    db = connect_db()
    req = request.get_json()

    r.table("matchTypes").insert(req["types"]).run(db)
    return jsonify(True)

@app.route("/set-selections/", methods=["POST"])
def set_selections():
    db = connect_db()
    req = request.get_json()

    r.table("selections").insert(req["selections"]).run(db)
    return jsonify(True)
