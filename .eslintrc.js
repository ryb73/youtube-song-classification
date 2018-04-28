module.exports = {
    extends: [
        "eslint:recommended",
        "plugin:react/recommended",
        "plugin:import/errors",
        "plugin:import/warnings",
    ],

    env: {
        browser: true,
        es6: true,
    },

    parserOptions: {
        ecmaVersion: 2018,
        sourceType: "module",
        ecmaFeatures: {
            jsx: true
        }
    },

    rules: {
        "linebreak-style": [
            "error",
            "unix"
        ],

        semi: [
            "error",
            "always"
        ],

        "no-unused-vars": [
            "warn",
            { vars: "all", args: "none" }
        ],

        eqeqeq: [ "error", "always" ],

        "no-console": "off",
        "no-unreachable": "warn",
        "no-debugger": "warn",

        "react/prop-types": "off",
    },

    globals: {
        CONFIG: true,
        gapi: true,
    },
};