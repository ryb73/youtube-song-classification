import rethinkdb as r
import jsoncfg
import os
import pandas as pd

fp = __file__

def connect_db():
    config = jsoncfg.load_config(os.path.join(os.path.dirname(fp), "config.json"))
    return r.connect(host=config.rethinkdb.host(), port=config.rethinkdb.port(), db=config.rethinkdb.db())

def get_data():
    db = connect_db()
    data = list(r.table("selections")
        .eq_join("searchId", r.table("searches"))
        .eq_join(r.row["left"]["videoId"], r.table("videos"))
        .eq_join(r.row["right"]["snippet"]["channelId"], r.table("youTubeChannels"))
        .map(format_doc)
        .run(db))
    data = [ { **row, "ytChannelSubscriberCount": int(row["ytChannelSubscriberCount"]) } for row in data ]
    return pd.DataFrame(data)

def get_features(data):
    # ideas
    # ard distance from vid upload date
    # y/m/d presensce in description
    # spotify duration distance from vid dur
    #
    # essential
    # album release date (ard) – clean year-only dates or drop date
    # missing values
    # categorize: ytCategoryId, ytDefinition

    return []

def get_labels(data):
    return []

def format_doc(doc):
    selection = doc["left"]["left"]["left"]
    search = doc["left"]["left"]["right"]
    video = doc["left"]["right"]
    channel = doc["right"]
    return {
        "selectionId": selection["id"],
        "selection": selection["value"],
        "searchIndex": r.branch(selection.has_fields("vidMeta"), selection["vidMeta"]["searchIndex"], None),
        "spotArtistName": search["track"]["artists"][0]["name"],
        "spotAlbumName": search["track"]["album"]["name"],
        "spotAlbumReleaseDate": search["track"]["album"]["release_date"],
        "spotAlbumReleaseDatePrecision": search["track"]["album"]["release_date_precision"],
        "spotDurationMs": search["track"]["duration_ms"],
        "spotExplicit": search["track"]["explicit"],
        "spotTrackName": search["track"]["name"],
        "ytDurationIso": video["contentDetails"]["duration"],
        "ytCaption": video["contentDetails"]["caption"],
        "ytDefinition": video["contentDetails"]["definition"],
        "ytLicensedContent": video["contentDetails"]["licensedContent"],
        "ytCategoryId": video["snippet"]["categoryId"],
        "ytChannelId": video["snippet"]["channelId"],
        "ytChannelName": video["snippet"]["channelTitle"],
        "ytDescription": video["snippet"]["description"],
        "ytPublishTimestamp": video["snippet"]["publishedAt"],
        "ytTitle": video["snippet"]["title"],
        "ytTags": r.branch(video["snippet"].has_fields("tags"), video["snippet"]["tags"], []),
        "ytCommentCount": r.branch(video["statistics"].has_fields("commentCount"), video["statistics"]["commentCount"], None),
        "ytDislikeCount": r.branch(video["statistics"].has_fields("dislikeCount"), video["statistics"]["dislikeCount"], None),
        "ytFavoriteCount": video["statistics"]["favoriteCount"],
        "ytLikeCount": r.branch(video["statistics"].has_fields("likeCount"), video["statistics"]["likeCount"], None),
        "ytViewCount": video["statistics"]["viewCount"],
        "ytChannelId": channel["id"],
        "ytChannelName": channel["snippet"]["title"],
        "ytChannelDescription": channel["snippet"]["description"],
        "ytChannelCommentCount": channel["statistics"]["commentCount"],
        "ytChannelSubscriberCount": channel["statistics"]["subscriberCount"],
        "ytChannelViewCount": channel["statistics"]["viewCount"],
        "videoId": video["id"]
    }

data = get_data()
X = data[[
    "searchIndex", "spotExplicit", "spotDurationMs", "ytChannelSubscriberCount",
    "ytChannelViewCount", "ytCommentCount", "ytDislikeCount", "ytFavoriteCount",
    "ytLicensedContent", "ytLikeCount", "ytViewCount"
]]
