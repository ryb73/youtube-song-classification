module.exports = {
    extends: [ "eslint:recommended", "plugin:react/recommended" ],

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
            "error",
            { vars: "all", args: "none" }
        ],

        eqeqeq: [ "error", "always" ],

        "no-console": 0
    },
};