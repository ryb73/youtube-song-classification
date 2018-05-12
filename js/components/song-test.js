import React from "react";
import autobind from "class-autobind";
import _ from "lodash";
import classNames from "classnames";
import update from "immutability-helper";
import { getYouTubeChannels, saveYouTubeChannels, getVideos, saveVideos, getMatchTypes, setSelections, addMatchTypes } from "../api-helper";

const nullMatch = "none";

export default class SongTest extends React.Component {
    constructor(props) {
        super(props);
        autobind(this);

        this.state = {
            track: null,
            channelDetails: null,
            videoDetails: null,
            vidMeta: {},
            toggledVideo: null,
            attributes: {},
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
        let { videoDetails, toggledVideo, channelDetails, attributes } = this.state;

        return _.map(videoDetails, (video) => {
            let toggled = video.id === toggledVideo;
            let className = classNames({
                toggled,
                match: this.isMatchSelected(attributes[video.id])
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
                    {this.renderAttributes(video.id)}
                </li>
            );
        });
    }

    isMatchSelected(attributes) {
        if(!attributes)
            return false;

        if(attributes.matchKind === nullMatch)
            return false;

        if(attributes.matchKind === "related")
            return true;

        return !!this.getMatchTypeValue(attributes);
    }

    renderAttributes(videoId) {
        let attributes = this.state.attributes[videoId] || this.createEmptyAttributes();
        let { matchKind } = attributes;

        return (
            <form className="selector">
                {this.renderBooleanAttributes(videoId)}
                <label>
                    <input type="radio" name="matchKind" value="none" checked={!matchKind || matchKind === nullMatch} onChange={this.setMatchKind.bind(this, videoId)} />
                    None
                </label>
                <label>
                    <input type="radio" name="matchKind" value="exact" checked={matchKind === "exact"} onChange={this.setMatchKind.bind(this, videoId)} />
                    Exact
                </label>
                <label>
                    <input type="radio" name="matchKind" value="alternate" checked={matchKind === "alternate"} onChange={this.setMatchKind.bind(this, videoId)} />
                    Alternate
                </label>
                <label>
                    <input type="radio" name="matchKind" value="related" checked={matchKind === "related"} onChange={this.setMatchKind.bind(this, videoId)} />
                    Related
                </label>
                {this.renderMatchTypeSelection(matchKind, videoId)}
            </form>
        );
    }

    renderBooleanAttributes(videoId) {
        let { audioOnly, hq } = this.getAttributes(videoId);
        return (
            <div>
                <label>
                    <input type="checkbox" checked={!!audioOnly} onClick={this.checkboxClicked.bind(this, "audioOnly", videoId)} />
                    Audio Only
                </label>
                <label>
                    <input type="checkbox" checked={!!hq} onClick={this.checkboxClicked.bind(this, "hq", videoId)} />
                    HQ
                </label>
            </div>
        );
    }

    getAttributes(videoId) {
        let { attributes } = this.state;
        return attributes[videoId] || this.createEmptyAttributes();
    }

    checkboxClicked(which, videoId, e) {
        // TODO: clean up
        let { attributes } = this.state;
        if(!attributes[videoId])
            attributes[videoId] = this.createEmptyAttributes();

        let updateParams = {
            [videoId]: { [which]: { $set: e.target.checked } }
        };

        if(which === "audioOnly" && attributes[videoId].matchKind === "exact" && e.target.checked)
            updateParams[videoId].matchType = { $set: "audioOnly" };

        this.setState({ attributes: update(attributes, updateParams) });
    }

    renderMatchTypeSelection(matchKind, videoId) {
        if(!this.state.matchTypes)
            return <i className="fa fa-spinner fa-pulse selector" />;

        let matchTypes = this.state.matchTypes[matchKind];
        if(!matchTypes)
            return null;

        let options = matchTypes.map(({ id, name }) =>
            <option value={id} key={id}>{name}</option>
        );

        let { matchType, otherValue } = this.state.attributes[videoId];

        let otherInput;
        if(matchType === "other")
            otherInput = <input type="text" value={otherValue}
                                onChange={this.otherValueChanged.bind(this, videoId)}
                                ref={this.otherInputMounted} />;

        return (
            <div>
                {otherInput}
                <select value={matchType} onChange={this.setMatchType.bind(this, videoId)}>
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
            attributes: update(this.state.attributes, {
                [videoId]: { otherValue: {
                    $set: e.target.value
                }}
            })
        });
    }

    setMatchType(videoId, e) {
        this.setState({
            attributes: update(this.state.attributes, {
                [videoId]: {
                    matchType: { $set: e.target.value },
                    otherValue: { $set: "" }
                }
            })
        });
    }

    setMatchKind(videoId, e) {
        let { attributes } = this.state;

        if(!attributes[videoId])
            attributes[videoId] = this.createEmptyAttributes();

        this.setState({
            attributes: update(this.state.attributes, {
                [videoId]: {
                    matchKind: { $set: e.target.value },
                    matchType: { $set: "other" },
                    otherValue: { $set: "" }
                }
            })
        });
    }

    createEmptyAttributes() {
        return { matchKind: nullMatch };
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
            attributes: {},
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

    getMatchTypeValue(attribute) {
        if(!attribute)
            return null;

        if(attribute.matchType === "other")
            return attribute.otherValue;

        return attribute.matchType;
    }

    nextSong() {
        let { attributes, videoDetails, track, vidMeta } = this.state;

        for(let videoId in videoDetails) {
            attributes[videoId] = attributes[videoId] || this.createEmptyAttributes();
        }

        this.saveOthers();

        let selectionValues = _.map(attributes, (attribute, videoId) => {
            return {
                ...attribute,
                otherValue: undefined,
                matchType: this.getMatchTypeValue(attribute),

                version: 2,
                videoId,
                vidMeta: vidMeta[videoId],
            };
        });

        setSelections(track.id, selectionValues);

        this.props.songIterator().then(this.setCurrentTrack);
    }

    saveOthers() {
        let { attributes } = this.state;

        let others = _.filter(attributes, ({ otherValue }) => !!otherValue);
        if(!others)
            return;

        let otherTypes = others.map(({ otherValue, matchKind }) => {
            return {
                id: otherValue,
                name: otherValue,
                kind: matchKind
            };
        });

        addMatchTypes(otherTypes);

        let updateParams = {
            exact: { $push: [] },
            alternate: { $push: [] }
        };
        for(let ot of otherTypes) {
            updateParams[ot.kind].$push.push(ot);
        }

        this.setState({
            matchTypes: update(this.state.matchTypes, updateParams)
        });
    }
}