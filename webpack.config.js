const path = require('path')
const process = require('process')
const webpack = require('webpack')

const BundleTracker = require('webpack-bundle-tracker')
const MiniCssExtractPlugin = require("mini-css-extract-plugin")

const env = process.env.NODE_ENV || 'development';

module.exports = {
    mode: env,
    context: __dirname,
    entry: './assets/index',

    output: {
        path: path.resolve('./static/dist/'),
        filename: "[name]-[hash].js"
    },

    module: {
        rules: [
            {
                test: /\.s([ca])ss$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    {
                        loader: 'css-loader'
                    },
                    {
                        loader: 'sass-loader',
                        options: {
                            sourceMap: env === 'development'
                        }
                    },
                ]
            },
            {
                test: /\.css$/,
                use: [
                    'style-loader',
                    'css-loader',
                ]
            },
            {
                test: /\.(png|svg|jpg|gif)$/,
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            name: 'img/[name].[ext]'
                        }
                    }
                ]
            },
			{
				test: /\.jsx?$/,
				exclude: /node_modules/,
				use: 'babel-loader'
			},
        ]
    },

    plugins: [
        new BundleTracker({
            filename: './webpack-stats.json'
        }),
        new MiniCssExtractPlugin({
            filename: "[name]-[hash].css",
        }),
    ]
}
