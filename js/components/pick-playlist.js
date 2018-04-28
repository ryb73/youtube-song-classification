import React from "react";
import autobind from "class-autobind";
import songIterator from "../song-iterator";

export default class PickPlaylist extends React.Component {
    constructor(props) {
        super(props);
        autobind(this);

        this.state = { playlists: null, loading: null };
    }

    render() {
        return (
            <div>
                <h3>Select playlist:</h3>
                {this.renderPlaylists()}
            </div>
        );
    }

    renderPlaylists() {
        if(!this.state.playlists) {
            setTimeout(this.loadPlaylists, 1);
            return <i className="fa fa-spinner fa-pulse" />;
        }

        let items = this.state.playlists.map((playlist) =>
            <li key={playlist.id}>
                <a href="#" onClick={this.playlistSelected.bind(this, playlist)}>{playlist.name}</a>
            </li>
        );

        return <ul>{items}</ul>;
    }

    async playlistSelected(playlist, e) {
        e.preventDefault();

        this.props.onPlaylistPicked(
            songIterator(this.props.spotify, playlist.owner.id, playlist)
        );
    }

    async loadPlaylists() {
        if(this.state.loading)
            return;

        this.setState({ loading: true });

        let next;
        let iterations = 0;
        let results = [];
        do {
            let resp = await this.props.spotify.getUserPlaylists({ limit: 50, offset: iterations * 50 });
            if(!resp.items) {
                alert("Error getting playlists");
                return;
            }

            results = results.concat(resp.items);

            next = resp.next;
            ++iterations;
        } while(next);

        this.setState({ playlists: results, loading: false });
    }
}