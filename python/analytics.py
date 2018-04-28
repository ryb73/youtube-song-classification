# let db = r.db("mophoAnalytics");
# db
#   .table("selections")
#   .eqJoin("searchId", db.table("searches"))
#   .eqJoin(r.row("left")("videoId"), db.table("videos"))
#   .eqJoin(r.row("right")("snippet")("channelId"), db.table("youTubeChannels"))
#   .map(function (doc) {
#     let selection = doc("left")("left")("left");
#     let search = doc("left")("left")("right");
#     let video = doc("left")("right");
#     let channel = doc("right");
#     return {
#       selectionId: selection("id"),
#       selection: selection("value"),
#       searchIndex: r.branch(selection.hasFields("vidMeta"), selection("vidMeta")("searchIndex"), ""),
#       spotArtistName: search("track")("artists")(0)("name"),
#       spotAlbumName: search("track")("album")("name"),
#       spotAlbumReleaseDate: search("track")("album")("release_date"),
#       spotAlbumReleaseDatePrecision: search("track")("album")("release_date_precision"),
#       spotDurationMs: search("track")("duration_ms"),
#       spotExplicit: search("track")("explicit"),
#       spotTrackName: search("track")("name"),
#       ytDurationIso: video("contentDetails")("duration"),
#       ytCaption: video("contentDetails")("caption"),
#       ytDefinition: video("contentDetails")("definition"),
#       ytLicensedContent: video("contentDetails")("licensedContent"),
#       ytCategoryId: video("snippet")("categoryId"),
#       ytChannelId: video("snippet")("channelId"),
#       ytChannelName: video("snippet")("channelTitle"),
#       ytDescription: video("snippet")("description"),
#       ytPublishTimestamp: video("snippet")("publishedAt"),
#       ytTitle: video("snippet")("title"),
#       ytTags: r.branch(video("snippet").hasFields("tags"), video("snippet")("tags"), []),
#       ytCommentCount: video("statistics")("commentCount"),
#       ytDislikeCount: video("statistics")("dislikeCount"),
#       ytFavoriteCount: video("statistics")("favoriteCount"),
#       ytLikeCount: video("statistics")("likeCount"),
#       ytViewCount: video("statistics")("viewCount"),
#       ytChannelId: channel("id"),
#       ytChannelName: channel("snippet")("title"),
#       ytChannelDescription: channel("snippet")("description"),
#       ytChannelCommentCount: channel("statistics")("commentCount"),
#       ytChannelSubscriberCount: channel("statistics")("subscriberCount"),
#       ytChannelViewCount: channel("statistics")("viewCount"),
#     };
#   })