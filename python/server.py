import rethinkdb as r
import jsoncfg
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

config = jsoncfg.load_config(os.path.join(os.path.dirname(__file__), "config.json"))

app = Flask(__name__)
CORS(app)

@app.route("/add-track/", methods=["POST"])
def ensure_track_exists():
    db = r.connect(host=config.rethinkdb.host(), port=config.rethinkdb.port(), db=config.rethinkdb.db())

    req = request.get_json()
    id = get_track_by_type_id(db, req["trackType"], req["track"]["id"])
    if id is not None:
        print("exists")
    else:
        print("doesn't exist, saving")
        id = r.table("tracks").insert(req).run(db).generated_keys[0]

    return id

def get_track_by_type_id(db, type, id):
    res = list(r.table("tracks").filter(r.row["trackType"] == type).filter(r.row["track"]["id"] == id).run(db))
    if len(res) < 1:
        return None
    return res[0]["id"]
