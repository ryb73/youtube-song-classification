/* eslint-env node */

const path              = require("path");

function rel(relPath) {
    return path.resolve(__dirname, relPath);
}

module.exports = {
    mode: "development",

    entry: {
        index: rel("js/index.js"),
    },

    output: {
        path: rel("html/js"),
        filename: "[name].js",
    },

    module: {
        rules: [{
            enforce: "pre",
            test: /\.jsx?$/,
            loader: "eslint-loader"
        }, {
            test: /\.jsx?$/,
            exclude: /node_modules/,
            loader: "babel-loader?cacheDirectory=true"
        }]
    },

    devtool: "source-map",
};
