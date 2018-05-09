import rethinkdb as r
import jsoncfg
import os
import pandas as pd
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from xgboost import XGBClassifier
from sklearn.preprocessing import Imputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.metrics import confusion_matrix, recall_score, precision_score, f1_score
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

fp = __file__


def connect_db():
    config = jsoncfg.load_config(os.path.join(
        os.path.dirname(fp), "config.json"))
    return r.connect(host=config.rethinkdb.host(), port=config.rethinkdb.port(), db=config.rethinkdb.db())


def get_data():
    db = connect_db()
    data = list(r.table("selections")
                .eq_join("searchId", r.table("searches"))
                .eq_join(r.row["left"]["videoId"], r.table("videos"))
                .eq_join(r.row["right"]["snippet"]["channelId"], r.table("youTubeChannels"))
                .map(format_doc)
                .run(db))

    data = [
        {**row,
         "ytChannelSubscriberCount": int(row["ytChannelSubscriberCount"]) if row["ytChannelSubscriberCount"] is not None else None,
         "ytChannelCommentCount": int(row["ytChannelCommentCount"]) if row["ytChannelCommentCount"] is not None else None,
         "ytChannelViewCount": int(row["ytChannelViewCount"]) if row["ytChannelViewCount"] is not None else None,
         "ytCommentCount": int(row["ytCommentCount"]) if row["ytCommentCount"] is not None else None,
         "ytDislikeCount": int(row["ytDislikeCount"]) if row["ytDislikeCount"] is not None else None,
         "ytFavoriteCount": int(row["ytFavoriteCount"]) if row["ytFavoriteCount"] is not None else None,
         "ytLikeCount": int(row["ytLikeCount"]) if row["ytLikeCount"] is not None else None,
         "ytViewCount": int(row["ytViewCount"]) if row["ytViewCount"] is not None else None,
         "containsArtist": row["spotArtistName"] in (row["ytTitle"] + " " + row["ytDescription"]),
         "containsAlbum": row["spotAlbumName"] in (row["ytTitle"] + " " + row["ytDescription"]),
         "containsTrack": row["spotTrackName"] in (row["ytTitle"] + " " + row["ytDescription"]),
         } for row in data]
    return pd.DataFrame(data)


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

def create_vectorizer():
    return TfidfVectorizer(analyzer = "word",   \
                            stop_words = "english",   \
                            max_features = 1000,
                            ngram_range=(1,2),
                            min_df=5,
                            sublinear_tf=True)


def get_scores(confusion, y, y_pred, y_factorization):
    df = pd.DataFrame({
        "recall": confusion.apply(lambda x: x[x.name] / x.sum(), axis=1),
        "precision": confusion.apply(lambda x: x[x.name] / x.sum())
    }).rename_axis(None)

    df.index = [ y_factorization[1][x] for x in df.index ]

    df.loc["totals"] = [
        recall_score(y, y_pred, average="micro"),
        precision_score(y, y_pred, average="micro"),
    ]

    return df

def cross_validate(classifier, X, y, y_factorization):
    print(classifier.__class__.__name__)

    my_pipeline = make_pipeline(Imputer(), classifier)
    y_pred = cross_val_predict(my_pipeline, X, y)

    confusion = pd.DataFrame(confusion_matrix(y, y_pred))
    confusion = confusion.rename_axis("actual", axis="rows").rename_axis("predicted", axis="columns")

    scores = get_scores(confusion, y, y_pred, y_factorization)

    print(confusion)
    print(scores)
    print()

    return (confusion, scores)

def main():
    data = get_data()
    data = data[(data.selection != "mashup") & (data.selection != "instrumental")]
    data.selection = data.selection.replace("lyricHD","LyricVideo")
    data.selection = data.selection.replace("proCover","cover")
    data.selection = data.selection.replace("drumCover","instrumentCover")
    data.selection = data.selection.replace("pianoCover","instrumentCover")
    data.selection = data.selection.replace("guitarCover","instrumentCover")
    data.selection = data.selection.replace("liveAcoustic","live")
    data.selection = data.selection.replace("liveAcousticHQ","liveInStudio")
    data.selection = data.selection.replace("cover","alternate")
    data.selection = data.selection.replace("instrumentCover","related")
    data.selection = data.selection.replace("remix","alternate")
    data.selection = data.selection.replace("acoustic","alternate")
    data.selection = data.selection.replace("liveAudio","live")
    data.selection = data.selection.replace("liveHD","live")
    data.selection = data.selection.replace("live","alternate")
    data.selection = data.selection.replace("liveInStudio","alternate")
    data.selection = data.selection.replace("LyricVideo","exact")
    data.selection = data.selection.replace("audioOnly","exact")
    data.selection = data.selection.replace("fanVideo","exact")
    data.selection = data.selection.replace("officialVideo","exact")
    data.selection = data.selection.replace("officialLyricVideo","exact")
    data = data.reset_index(drop=True)

    X = pd.get_dummies(data[[
        "searchIndex", "spotExplicit", "spotDurationMs", "ytChannelSubscriberCount",
        "ytChannelViewCount", "ytCommentCount", "ytDislikeCount", "ytFavoriteCount",
        "ytLicensedContent", "ytLikeCount", "ytViewCount",
        "ytDefinition", "ytCaption", "ytChannelId", "containsArtist", "containsAlbum", "containsTrack"
    ]])

    y_factorization = pd.factorize(data.selection)
    y = y_factorization[0]

    full_vectorizer = create_vectorizer()
    full_vectorizer.fit(data.ytDescription).fit(data.ytTitle)

    description_bag = full_vectorizer.transform(data.ytDescription)
    description_bag_sdf = pd.SparseDataFrame(description_bag, columns=full_vectorizer.get_feature_names(), default_fill_value=0)

    title_bag = full_vectorizer.transform(data.ytTitle)
    title_bag_sdf = pd.SparseDataFrame(title_bag, columns=full_vectorizer.get_feature_names(), default_fill_value=0)

    X = pd.concat([X, description_bag_sdf, title_bag_sdf], axis=1)

    models = [
        RandomForestClassifier(n_estimators=200, max_depth=3),
        LinearSVC(),
        MultinomialNB(),
        LogisticRegression(),
        XGBClassifier()
    ]

    for model in models:
        confusion, scores = cross_validate(model, X, y, y_factorization)

    return (data, X, y, confusion, scores)

data, X, y, confusion, scores = main()