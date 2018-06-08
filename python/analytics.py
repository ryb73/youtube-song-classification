import rethinkdb as r
import jsoncfg
import os
import re
import pandas as pd
import numpy as np
from math import log
# from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from xgboost import XGBClassifier
from sklearn.preprocessing import Imputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
import matplotlib.pyplot as plt

fp = __file__


def connect_db():
    config = jsoncfg.load_config(os.path.join(
        os.path.dirname(fp), "config.json"))
    return r.connect(host=config.rethinkdb.host(), port=config.rethinkdb.port(), db=config.rethinkdb.db())


def get_data():
    db = connect_db()
    data = list(r.table("selections")
                .filter({"version": 2})
                .eq_join("searchId", r.table("searches"))
                .eq_join(r.row["left"]["videoId"], r.table("videos"))
                .eq_join(r.row["right"]["snippet"]["channelId"], r.table("youTubeChannels"))
                .map(format_doc)
                .run(db))

    data = [
        {**row,
            "ytChannelSubscriberCount": try_log(int(row["ytChannelSubscriberCount"])) if row["ytChannelSubscriberCount"] is not None else None,
            # "ytChannelCommentCount": try_log(int(row["ytChannelCommentCount"])) if row["ytChannelCommentCount"] is not None else None,
            "ytChannelViewCount": try_log(int(row["ytChannelViewCount"])) if row["ytChannelViewCount"] is not None else None,
            "ytCommentCount": try_log(int(row["ytCommentCount"])) if row["ytCommentCount"] is not None else None,
            "ytDislikeCount": try_log(int(row["ytDislikeCount"])) if row["ytDislikeCount"] is not None else None,
            # "ytFavoriteCount": try_log(int(row["ytFavoriteCount"])) if row["ytFavoriteCount"] is not None else None,
            "ytLikeCount": try_log(int(row["ytLikeCount"])) if row["ytLikeCount"] is not None else None,
            "ytViewCount": try_log(int(row["ytViewCount"])) if row["ytViewCount"] is not None else None,
            # "containsArtist": row["spotArtistName"] in (row["ytTitle"] + " " + row["ytDescription"]),
            # "containsAlbum": row["spotAlbumName"] in (row["ytTitle"] + " " + row["ytDescription"]),
            # "containsTrack": row["spotTrackName"] in (row["ytTitle"] + " " + row["ytDescription"]),
            "ytDescription": tokenize_dynamic_names(row, row["ytDescription"]),
            "ytTitle": tokenize_dynamic_names(row, row["ytTitle"]),
            # "ytChannelName": tokenize_dynamic_names(row, row["ytChannelName"], True),
            "ytChannelDescription": tokenize_dynamic_names(row, row["ytChannelDescription"]),
            "ytTags": tokenize_dynamic_names(row, ", ".join(row["ytTags"])),
            "isVevo": "VEVO" in row["ytChannelName"].upper(),
        } for row in data]

    # ideas
    # ard distance from vid upload date
    # y/m/d presensce in description
    # spotify duration distance from vid dur
    # album release date (ard) – clean year-only dates or drop date
    # missing values
    # categorize: ytCategoryId
    # record label matching to yt channel

    return pd.DataFrame(data)

def try_log(n):
    if n == 0:
        return 0
    return log(n)

def tokenize_dynamic_names(row, text, no_spaces=False):
    spotTrackName = row["spotTrackName"]
    if no_spaces:
        spotTrackName = spotTrackName.replace(" ", "")
    regex = re.compile(re.escape(spotTrackName), re.IGNORECASE)
    text = regex.sub("<tokenTrackName>", text)

    spotArtistName = row["spotArtistName"]
    if no_spaces:
        spotArtistName = spotArtistName.replace(" ", "")
    regex = re.compile(re.escape(spotArtistName), re.IGNORECASE)
    text = regex.sub("<tokenArtistName>", text)

    spotAlbumName = row["spotAlbumName"]
    if no_spaces:
        spotAlbumName = spotAlbumName.replace(" ", "")
    regex = re.compile(re.escape(spotAlbumName), re.IGNORECASE)
    text = regex.sub("<tokenAlbumName>", text)

    return text

def format_doc(doc):
    selection = doc["left"]["left"]["left"]
    search = doc["left"]["left"]["right"]
    video = doc["left"]["right"]
    channel = doc["right"]
    return {
        "selectionId": selection["id"],
        "matchKind": selection["matchKind"],
        "matchType": r.branch(selection.has_fields("matchType"), selection["matchType"], None),
        "audioOnly": r.branch(selection.has_fields("audioOnly"), selection["audioOnly"], False),
        "hq": r.branch(selection.has_fields("hq"), selection["hq"], False),
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

def create_vectorizer():
    return TfidfVectorizer(analyzer = "word",   \
                            stop_words = "english",   \
                            max_features = 2000,
                            ngram_range=(1,3),
                            min_df=5)


def cross_validate(classifier, X, y, y_factorization):
    print(classifier.__class__.__name__)

    my_pipeline = make_pipeline(Imputer(), classifier)
    y_pred = cross_val_predict(my_pipeline, X, y)

    confusion = pd.DataFrame(confusion_matrix(y, y_pred))
    confusion = confusion.rename_axis("actual", axis="rows").rename_axis("predicted", axis="columns")

    print(confusion)
    print(classification_report(y, y_pred, target_names=y_factorization[1]))
    print()

    return confusion, y_pred

def kind_model(data, bags):
    X = pd.get_dummies(data[[
        "searchIndex", "spotExplicit", "spotDurationMs", "ytChannelSubscriberCount",
        "ytChannelViewCount", "ytCommentCount", "ytDislikeCount", "ytFavoriteCount",
        "ytLicensedContent", "ytLikeCount", "ytViewCount",
        "ytDefinition", "ytCaption", #"ytChannelId", # "containsArtist", "containsAlbum", "containsTrack"
    ]])
    X = pd.concat([ X.to_sparse(), *bags ], axis=1)

    y_factorization = pd.factorize(data.matchKind)
    y = y_factorization[0]

    return run_models(X, y, y_factorization)

def exact_type_model(data, bags):
    filtered_data = data[(data["matchKind"] == "exact") &
        (data["matchType"] != "lyricsOtherLang")]

    filtered_data = filtered_data.reset_index(drop=True)
    non_audio = filtered_data[filtered_data["matchType"] != "audioOnly"].index
    audio = np.random.choice(filtered_data[filtered_data["matchType"] == "audioOnly"].index, 70, replace=False)
    filtered_data = pd.concat([ filtered_data.iloc[non_audio], filtered_data.iloc[audio] ])
    filtered_data = filtered_data.reset_index(drop=True)

    filtered_bags = [ sdf.iloc[filtered_data.index.intersection(sdf.index)] for sdf in bags ]

    X = pd.get_dummies(filtered_data[[
        "searchIndex", "spotExplicit", "spotDurationMs", "ytChannelSubscriberCount",
        "ytChannelViewCount", "ytCommentCount", "ytDislikeCount", "ytFavoriteCount",
        "ytLicensedContent", "ytLikeCount", "ytViewCount",
        "ytDefinition", "ytCaption", #"ytChannelId", # "containsArtist", "containsAlbum", "containsTrack"
    ]])
    X = pd.concat([X.to_sparse(), *filtered_bags ], axis=1)

    y_factorization = pd.factorize(filtered_data.matchType)
    y = y_factorization[0]

    results = run_models(X, y, y_factorization)
    results["combined"] = pd.concat([
        filtered_data.to_sparse(),
        X,
        pd.DataFrame(y, columns=["y"]).to_sparse(),
        pd.DataFrame(results["prediction"], columns=["prediction"]).to_sparse()
    ], axis=1)

    return results

def run_models(X, y, y_factorization):
    models = [
        # RandomForestClassifier(n_estimators=1000, max_depth=4),
        # LinearSVC(),
        # MultinomialNB(),
        # LogisticRegression(),
        XGBClassifier()
    ]

    for model in models:
        confusion, prediction = cross_validate(model, X, y, y_factorization)

    return {
        "X": X,
        "y": y,
        "confusion": confusion,
        "prediction": prediction
    }

def main():
    data = get_data()
    # data = data[(data.selection != "mashup") & (data.selection != "instrumental")]
    # data.selection = data.selection.replace("lyricHD","LyricVideo")
    # data.selection = data.selection.replace("proCover","cover")
    # data.selection = data.selection.replace("drumCover","instrumentCover")
    # data.selection = data.selection.replace("pianoCover","instrumentCover")
    # data.selection = data.selection.replace("guitarCover","instrumentCover")
    # data.selection = data.selection.replace("liveAcoustic","live")
    # data.selection = data.selection.replace("liveAcousticHQ","liveInStudio")
    # data.selection = data.selection.replace("cover","alternate")
    # data.selection = data.selection.replace("instrumentCover","related")
    # data.selection = data.selection.replace("remix","alternate")
    # data.selection = data.selection.replace("acoustic","alternate")
    # data.selection = data.selection.replace("liveAudio","live")
    # data.selection = data.selection.replace("liveHD","live")
    # data.selection = data.selection.replace("live","alternate")
    # data.selection = data.selection.replace("liveInStudio","alternate")
    # data.selection = data.selection.replace("LyricVideo","exact")
    # data.selection = data.selection.replace("audioOnly","exact")
    # data.selection = data.selection.replace("fanVideo","exact")
    # data.selection = data.selection.replace("officialVideo","exact")
    # data.selection = data.selection.replace("officialLyricVideo","exact")
    data = data[data["matchKind"] != "related"]
    data = data.reset_index(drop=True)

    full_vectorizer = create_vectorizer()
    full_vectorizer\
        .fit(data.ytDescription)\
        .fit(data.ytTitle)\
        .fit(data.ytChannelDescription)\
        .fit(data.ytTags)

    bags = [
        vectorize(full_vectorizer, data.ytDescription, "descBag"),
        vectorize(full_vectorizer, data.ytTitle, "titleBag"),
        vectorize(full_vectorizer, data.ytChannelDescription, "chanDescBag"),
        vectorize(full_vectorizer, data.ytTags, "tagsBag"),
    ]

    results = {}
    results["kind"] = kind_model(data, bags)
    results["typeExact"] = exact_type_model(data, bags)

    return data, results

def vectorize(vectorizer, column, column_name):
    bag = vectorizer.transform(column)
    return pd.SparseDataFrame(bag, columns=[ column_name + " " + name for name in vectorizer.get_feature_names() ], default_fill_value=0)

data, results = main()

comb = results["typeExact"]["combined"]
comb = comb.loc[:,~comb.columns.duplicated()]
comb[(comb["matchType"] == "officialVideo") & (comb["prediction"] != 2)].to_dense().to_csv("out.csv", encoding='utf-8')

# pd.DataFrame({k: v for k, v in comb.groupby('matchType').ytChannelViewCount}).plot.hist(stacked=True)