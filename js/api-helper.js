import superagent from "superagent";

export async function getTracksToProcess(tracks) {
    let { body } = await superagent.post(getApiUrlBase() + "/get-tracks-to-process/")
        .send({ trackType: "spotify", tracks });
    return body;
}

export async function saveYouTubeChannels(channels) {
    return await superagent.post(getApiUrlBase() + "/save-youtube-channels/")
        .send({ channels });
}

export async function getYouTubeChannels(channelIds) {
    let { body } = await superagent.get(getApiUrlBase() + "/get-youtube-channels/")
        .query({ channelIds });

    return body;
}

export async function saveVideos(videos) {
    return await superagent.post(getApiUrlBase() + "/save-videos/")
        .send({ videos });
}

export async function getVideos(videoIds) {
    let { body } = await superagent.get(getApiUrlBase() + "/get-videos/")
        .query({ videoIds });

    return body;
}

export async function getMatchTypes() {
    let { body } = await superagent.get(getApiUrlBase() + "/get-match-types/");
    return body;
}

export async function setSelections(searchId, selections) {
    selections = selections.map(selection => {
        return { ...selection, searchId };
    });

    return await superagent.post(getApiUrlBase() + "/set-selections/")
        .send({ selections });
}

export async function addMatchTypes(types) {
    return await superagent.post(getApiUrlBase() + "/add-match-types/")
        .send({ types });
}

function getApiUrlBase() {
    let { secure, host, port } = CONFIG.api;
    let protocol = secure ? "https" : "http";
    return `${protocol}://${host}:${port}`;
}