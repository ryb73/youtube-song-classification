import React from "react";
import autobind from "class-autobind";

export default class SongText extends React.Component {
    constructor(props) {
        super(props);
        autobind(this);

        this.state = { loading: true };

        props.songIterator().then(this.setCurrentTrack);
    }

    render() {
        if(this.state.loading)
            return "Loading";

        return <pre>{JSON.stringify(this.state.track, null, 2)}</pre>;
    }

    setCurrentTrack(track) {
        this.setState({ loading: false, track });
    }
}