/* eslint-env node */

const path                = require("path");
const ConfigWebpackPlugin = require("config-webpack");

function rel(relPath) {
    return path.resolve(__dirname, relPath);
}

module.exports = {
    mode: "development",

    entry: {
        index: [ "babel-polyfill", rel("js/index.js") ],
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

    plugins: [
        new ConfigWebpackPlugin()
    ],

    devtool: "source-map",
};
