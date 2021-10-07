import {createApp, reactive} from "petite-vue"

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

        calendarURL,
    })

    createApp({
        store,

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
        })
    }

    setInterval(updateStreams, 30_000)
    updateStreams()
})
