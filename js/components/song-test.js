import React from "react";
import autobind from "class-autobind";
import _ from "lodash";
import classNames from "classnames";
import update from "immutability-helper";
import { getYouTubeChannels, saveYouTubeChannels, getVideos, saveVideos, getMatchTypes, setSelections, addMatchTypes } from "../api-helper";

export default class SongText extends React.Component {
    constructor(props) {
        super(props);
        autobind(this);

        this.state = {
            track: null,
            channelDetails: null,
            videoDetails: null,
            vidMeta: {},
            toggledVideo: null,
            selections: {},
            matchTypes: null,
            progress: null
        };

        props.songIterator().then(this.setCurrentTrack);
        this.loadMatchTypes();
    }

    render() {
        let { track } = this.state;

        if(!track)
            return "Loading";

        return (
            <div className="song-test">
                <div>
                    {this.renderProgress()}
                    Searching for {track.query}
                </div>

                <ul>
                    {this.renderVideoList()}
                </ul>
            </div>
        );
    }

    renderProgress() {
        if(!this.state.progress)
            return;

        let { current, total } = this.state.progress;
        return (
            <div className="progress">
                <button type="button" onClick={this.nextSong}>Next</button>
                {current} / {total}
            </div>
        );
    }

    renderVideoList() {
        let { videoDetails, toggledVideo, channelDetails } = this.state;

        return _.map(videoDetails, (video) => {
            let toggled = video.id === toggledVideo;
            let className = classNames({
                toggled,
                untoggled: !toggled,
                match: this.getSelectionValue(this.state.selections[video.id])
            });

            let { description, channelId } = video.snippet;
            let channelName = channelDetails[channelId].snippet.title;

            let player;
            if(toggled) {
                let embedSrc = `https://www.youtube.com/embed/${video.id}?autoplay=1`;
                player = <iframe type="text/html" width="640" height="360"
                                 src={embedSrc} frameBorder="0" />;

            } else if(description.length > 100) {
                description = description.substring(0, 100) + "...";
            }

            return (
                <li key={video.id} className={className} onClick={this.toggleVideo.bind(this, video.id)}>
                    <h3 className="title">{video.snippet.title}</h3>
                    <p className="description">{description}</p>
                    <p><strong>Channel:</strong> {channelName}</p>
                    {player}
                    {this.renderSelection(video.id)}
                </li>
            );
        });
    }

    renderSelection(videoId) {
        if(!this.state.matchTypes)
            return <i className="fa fa-spinner fa-pulse selector" />;

        let options = this.state.matchTypes.map(({ id, name }) =>
            <option value={id} key={id}>{name}</option>
        );

        let selection = this.state.selections[videoId] || {id:""};

        let otherInput;
        if(selection.id === "other")
            otherInput = <input type="text" value={selection.otherValue}
                                onChange={this.otherValueChanged.bind(this, videoId)}
                                ref={this.otherInputMounted} />;

        return (
            <div className="selector">
                {otherInput}
                <select className="selector" value={selection.id} onChange={this.setSelection.bind(this, videoId)}>
                    <option value="">No Match</option>
                    {options}
                    <option value="other">Other</option>
                </select>
            </div>
        );
    }

    otherInputMounted(elem) {
        if(elem)
            elem.focus();
    }

    otherValueChanged(videoId, e) {
        this.setState({
            selections: update(this.state.selections, {
                [videoId]: { otherValue: {
                    $set: e.target.value
                }}
            })
        });
    }

    setSelection(videoId, e) {
        this.setState({
            selections: update(this.state.selections, {
                [videoId]: { $set: { id: e.target.value, otherValue: "" } }
            })
        });
    }

    toggleVideo(videoId, e) {
        if(e.target.tagName.toLowerCase() !== "li")
            return;

        this.setState({
            toggledVideo: this.state.toggledVideo === videoId ? null : videoId
        });
    }

    async setCurrentTrack(track) {
        if(!track)
            alert("done!");

        let searchResults = await gapi.client.youtube.search.list({
            q: track.query,
            part: "snippet",
            maxResults: CONFIG.youtube.searchMaxResults
        });

        let videoIds = _.map(searchResults.result.items, "id.videoId");
        let videoDetails = await this.getVideoDetails(videoIds);

        let vidMeta = {};
        for(let i = 0; i < videoIds.length; ++i) {
            vidMeta[videoIds[i]] = { searchIndex: i };
        }

        let channelIds = _(videoDetails).map("snippet.channelId")
            .uniq().value();

        this.setState({
            track, videoDetails, vidMeta,
            channelDetails: await this.getChannelDetails(channelIds),
            selections: {},
            progress: track.progress,
            toggledVideo: null,
        });
    }

    async getVideoDetails(videoIds) {
        let { missingVideoIds, matchingVideos } = await getVideos(videoIds);

        let newVideos = {};
        if(missingVideoIds.length > 0) {
            let resp = await gapi.client.youtube.videos.list({
                part: "snippet,contentDetails,statistics,player",
                id: videoIds.join(",")
            });

            await saveVideos(resp.result.items);

            newVideos = _.keyBy(resp.result.items, "id");
        }

        return _.assign(_.keyBy(matchingVideos, "id"), newVideos);
    }

    async getChannelDetails(channelIds) {
        let { missingChannelIds, matchingChannels } = await getYouTubeChannels(channelIds);

        let newChannels = {};
        if(missingChannelIds.length > 0) {
            let resp = await gapi.client.youtube.channels.list({
                part: "snippet,statistics",
                id: missingChannelIds.join(",")
            });

            await saveYouTubeChannels(resp.result.items);

            newChannels = _.keyBy(resp.result.items, "id");
        }

        return _.assign(_.keyBy(matchingChannels, "id"), newChannels);
    }

    async loadMatchTypes() {
        this.setState({
            matchTypes: await getMatchTypes()
        });
    }

    getSelectionValue(selection) {
        if(!selection)
            return null;

        if(selection.id === "other")
            return selection.otherValue;

        return selection.id;
    }

    nextSong() {
        let { selections, videoDetails, track, vidMeta } = this.state;

        for(let videoId in videoDetails) {
            selections[videoId] = selections[videoId] || {id:""};
        }

        this.saveOthers();

        let selectionValues = _.map(selections, (selection, videoId) => {
            return {
                videoId,
                value: this.getSelectionValue(selection),
                vidMeta: vidMeta[videoId]
            };
        });

        setSelections(track.id, selectionValues);

        this.props.songIterator().then(this.setCurrentTrack);
    }

    saveOthers() {
        let { selections, matchTypes } = this.state;

        let others = _(selections)
            .map("otherValue")
            .filter()
            .value();

        if(!others)
            return;

        let otherTypes = others.map(v => { return { id: v, name: v }; });

        addMatchTypes(otherTypes);

        this.setState({
            matchTypes: matchTypes.concat(otherTypes)
        });
    }
}