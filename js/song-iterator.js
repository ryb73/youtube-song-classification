import _ from "lodash";
import { getTracksToProcess } from "./api-helper";

export default function songIterator(spotify, userId, playlist) {
    let trackBuffer = [];
    const limit = 2;
    let current = 0;

    const totalTracks = playlist.tracks.total;
    const playlistId = playlist.id;

    let offsetQueue = generateOffsetQueue(totalTracks, limit);

    return async function() {
        if(trackBuffer.length < 1) {
            let offset = offsetQueue.pop();

            let { items } = await spotify.getPlaylistTracks(
                userId, playlistId, { limit, offset }
            );
            if(items.length < 1)
                return null;

            let { searches, skipped } = await getTracksToProcess(_.map(items, "track"));
            if(searches.length < 1)
                return null;

            trackBuffer = searches;
            current += skipped;
        }

        ++current;
        let { id, query } = trackBuffer.shift();

        return { id, query, progress: { current, total: totalTracks } };
    };
}

function generateOffsetQueue(totalTracks, pageSize) {
    return _.shuffle(
        new Array(Math.floor(totalTracks / pageSize)).fill(pageSize)
            .map((v, i) => v * i)
    );
}
