import superagent from "superagent";

export default function songIterator(spotify, userId, playlistId) {
    let trackBuffer = [];
    let offset = 0;
    const limit = 10;

    return async function() {
        do {
            if(trackBuffer.length < 1) {
                let resp = await spotify.getPlaylistTracks(userId, playlistId, { limit, offset });
                trackBuffer = resp.items;
                if(resp.items.length < 1)
                    return null;

                offset += limit;
            }
        } while(dropAlreadyProcessed(trackBuffer) < 1);

        return saveTrack(trackBuffer.shift().track);
    };
}

function getApiUrlBase() {
    let { secure, host, port } = CONFIG.api;
    let protocol = secure ? "https" : "http";
    return `${protocol}://${host}:${port}`;
}

async function saveTrack(track) {
    await superagent.post(getApiUrlBase() + "/add-track/")
        .send({ trackType: "spotify", track });

    return track.id;
}

function dropAlreadyProcessed(tracks) {
    // TODO: implement
    return tracks.length;
}