import {createApp, reactive, nextTick} from "petite-vue"

import fetch from "../common/fetch"
import {Interval} from "luxon"
import {selectUnit} from "@formatjs/intl-utils"
import tinycolor from "tinycolor2"

document.addEventListener("DOMContentLoaded", () => {
    const streamsContainer = document.getElementById("js-home-live-and-upcoming")
    if (!streamsContainer) return

    const streamsLiveURL = streamsContainer.getAttribute("data-content-api")
    const calendarURL = streamsContainer.getAttribute("data-calendar-url")
    const raidAPI = streamsContainer.getAttribute("data-raid-api")

    const formatTimeShort = new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
    })

    const formatRelativeTime = new Intl.RelativeTimeFormat(undefined, {
        numeric: "auto",
        style: "long",
    })

    const store = reactive({
        live: [],
        scheduled: [],
        total_spectators: 0,
        loading: true,

        preview_open: false,
        preview_streamer: null,

        calendarURL,
    })

    let twitchPlayer = null

    createApp({
        store,

        /**
         * Opens the stream preview modal for the given streamer.
         * @param streamer The streamer object.
         */
        showPreview(streamer) {
            store.preview_streamer = streamer
            store.preview_open = true

            nextTick(() => {
                // We need to create a new player because the modale was never
                // opened before.
                if (!twitchPlayer) {
                    twitchPlayer = new Twitch.Embed("js-twitch-preview", {
                        width: "100%",
                        height: "100%",
                        autoplay: true,
                        channel: streamer.twitch_login,
                        layout: "video-with-chat",
                        theme: "dark",
                        parent: ["pogscience-stream.com"],
                    })
                }

                // We can only change the channel and play.
                else {
                    twitchPlayer.setChannel(streamer.twitch_login)
                    twitchPlayer.play()
                }
            })
        },

        /**
         * Closes the open stream preview modal, if any.
         */
        hidePreview() {
            store.preview_open = false
            if (twitchPlayer) {
                twitchPlayer.pause()
            }
        },

        /**
         * Raids a streamer.
         * @param streamer The streamer object.
         */
        raid(streamer) {
            fetch(raidAPI.replace("TWITCH_LOGIN", streamer.twitch_login), { method: "POST"}).then(r => r.json()).then(console.log)
        },

        /**
         * Returns the text color to use on the gradient buttons for the given
         * streamer.
         * @param streamer The streamer.
         * @return {string} The color to use for the text.
         */
        streamerButtonTextColour(streamer) {
            return tinycolor.mostReadable(
                tinycolor.mix(streamer.colours_hsl_css[0], streamer.colours_hsl_css[1]),
                ["#faf3f3", "#363636"],
                {
                    includeFallbackColors: true,
                    level: "AAA",
                    size: "small"
                },
            ).toHexString()
        },

        /**
         * Capitalizes a string.
         * @param str The string.
         * @returns {string} A capitalized version of the string, with the first
         *                   unicode point capitalized (if it can be) and the
         *                   remaining left as-is.
         */
        capitalize(str) {
            return str.replace(/^\p{CWU}/u, char => char.toLocaleUpperCase());
        },

        /**
         * Format a datetime string in hh:mm.
         * @param date A date string in ISO format (or anything the Date
         *             constructor accepts).
         * @returns {string} The formatted hour.
         */
        shortTime(date) {
            return formatTimeShort.format(new Date(date))
        },

        /**
         * Formats a date relatively (e.g. “tomorrow”, “in 2 hours”, “in 10 minutes”…)
         * @param date A date string in ISO format (or anything the Date
         *             constructor accepts).
         * @returns {string} The formatted time.
         */
        relativeTime(date) {
            const diff = selectUnit(new Date(date))
            return formatRelativeTime.format(diff.value, diff.unit)
        },

        /**
         * Formats the given duration, in hh:mm format.
         * @param seconds The amount of seconds.
         * @returns {string} The formatted duration, in hh:mm.
         */
        since(seconds) {
            const d = Interval.before(new Date(), parseInt(seconds) * 1000)
                .toDuration(['hours', 'minutes']).toObject()

            return Math.trunc(d.hours).toString().padStart(2, '0')
                + "h"
                + Math.trunc(d.minutes).toString().padStart(2, '0')
        }
    }).mount("#js-home-live-and-upcoming")

    function updateStreams() {
        fetch(streamsLiveURL).then(r => r.json()).then(data => {
            store.live = data.live
            store.scheduled = data.scheduled
            store.total_spectators = data.live.reduce((all, cur) => cur.live_spectators + all, 0)

            store.loading = false

            // Updates the twitch preview, mainly spectators count, if any
            if (store.preview_streamer) {
                for (const streamer of data.live) {
                    if (store.preview_streamer.twitch_login === streamer.twitch_login) {
                        store.preview_streamer = streamer
                        break
                    }
                }
            }
        })
    }

    setInterval(updateStreams, 30_000)
    updateStreams()
})
