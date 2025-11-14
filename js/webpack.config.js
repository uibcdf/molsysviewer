// js/webpack.config.js
const path = require("path");

module.exports = {
  mode: "development",
  entry: "./src/index.ts",
  output: {
    filename: "index.js",
    path: path.resolve(__dirname, "lib"),
    libraryTarget: "amd",
    publicPath: "",
  },
  devtool: "source-map",
  resolve: {
    extensions: [".ts", ".js"],
    fallback: {
      fs: false,
      path: false,
      crypto: false,
    },
  },
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
      {
        test: /\.(png|jpe?g|gif)$/i,
        type: "asset/resource",
      },
    ],
  },
  externals: [
    "@jupyter-widgets/base",
    "@jupyterlab/application",
  ],
};

