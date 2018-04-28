import React      from "react";
import ReactDOM   from "react-dom";
import Spotify    from "spotify-web-api-js";
import qs         from "qs";
import Main       from "./components/main";

async function main() {
    if(!location.hash) {
        location.href = "https://accounts.spotify.com/authorize?client_id=" + CONFIG.spotify.clientId +
            `&redirect_uri=${escape(location.href.split("#")[0])}&scope=playlist-read-private&response_type=token`;
        return;
    }

    let accessToken = getAccessCodeFromHash();
    if(!accessToken) {
        alert("No access token found");
        return;
    }

    location.hash = "";

    let spotify = new Spotify();
    spotify.setAccessToken(accessToken);

    await loadGoogleApi();

    ReactDOM.render(<Main spotify={spotify} />, document.getElementById("container"));
}

function loadGoogleApi() {
    return gapi.client.init({
        "apiKey": CONFIG.youtube.apiKey,
        "discoveryDocs": ["https://www.googleapis.com/discovery/v1/apis/youtube/v3/rest"],
    });
}

function getAccessCodeFromHash() {
    return qs.parse(location.hash.substring(1)).access_token;
}

gapi.load("client", main);
