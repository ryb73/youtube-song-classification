import React from "react";
import autobind from "class-autobind";
import PickPlaylist from "./pick-playlist";
import SongTest from "./song-test";

export default class Main extends React.Component {
    constructor(props) {
        super(props);
        autobind(this);

        this.state = { songIterator: null };
    }

    render() {
        if(!this.state.songIterator)
            return <PickPlaylist spotify={this.props.spotify} onPlaylistPicked={this.playlistPicked} />;

        return <SongTest songIterator={this.state.songIterator} />;
    }

    playlistPicked(songIterator) {
        this.setState({ songIterator });
    }
}
