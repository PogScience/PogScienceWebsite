import {createApp, reactive, nextTick} from "petite-vue"

import fetch from "../common/fetch"
import {Interval} from "luxon";
import {selectUnit} from "@formatjs/intl-utils";

document.addEventListener("DOMContentLoaded", () => {
    const streamsContainer = document.getElementById("js-home-live-and-upcoming")
    if (!streamsContainer) return

    const streamsLiveURL = streamsContainer.getAttribute("data-content-api")
    const calendarURL = streamsContainer.getAttribute("data-calendar-url")

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

        hidePreview() {
            store.preview_open = false
            if (twitchPlayer) {
                twitchPlayer.pause()
            }
        },

        capitalize(str) {
            return str.replace(/^\p{CWU}/u, char => char.toLocaleUpperCase());
        },

        shortTime(date) {
            return formatTimeShort.format(new Date(date))
        },

        relativeTime(date) {
            const diff = selectUnit(new Date(date))
            return formatRelativeTime.format(diff.value, diff.unit)
        },

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
