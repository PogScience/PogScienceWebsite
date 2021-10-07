import { h } from 'preact'

import {Calendar} from '@fullcalendar/core'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import listPlugin from '@fullcalendar/list'
import resourceTimelinePlugin from '@fullcalendar/resource-timeline';

document.addEventListener("DOMContentLoaded", () => {
    const calendarContainer = document.getElementById("js-calendar-grid")
    if (!calendarContainer) return

    const eventSourceURL = calendarContainer.getAttribute("data-events-source")
    const streamersResourcesURL = calendarContainer.getAttribute("data-streamers-resources")
    const fmt_weekday = new Intl.DateTimeFormat('fr', { weekday: 'long' })
    const capitalize = text => text.charAt(0).toUpperCase() + text.slice(1)

    const calendar = new Calendar(calendarContainer, {
        schedulerLicenseKey: 'GPL-My-Project-Is-Open-Source',
        plugins: [dayGridPlugin, timeGridPlugin, listPlugin, resourceTimelinePlugin],

        initialView: 'timeGridWeek',

        headerToolbar: {
          left: 'title',
          center: '',
          right: 'timeGridWeek,dayGridMonth,listYear,resourceTimelineWeek today prev,next'
        },

        buttonText: {
          dayGridMonth: 'Par mois',
          timeGridWeek: 'Par semaine',
          listYear: 'Tous les streams',
          resourceTimelineWeek: "Chronologie",
          today: "Aujourd'hui"
        },

        views: {
            resourceTimelineWeek: {
                slotDuration: "00:15"
            },
        },

        locale: 'fr',
        firstDay: 1,

        contentHeight: "auto",

        nowIndicator: true,

        // expandRows: true,
        stickyHeaderDates: true,
        stickyFooterScrollbar: true,

        allDaySlot: false,
        slotEventOverlap: false,

        eventContent: info => {
            const streamer = info.event.extendedProps.streamer
            const c = streamer.colours_hsl ? streamer.colours_hsl[0] : null
            const bg_color = c ? `hsl(${c[0]}, ${Math.min(c[1] + 60, 100)}%, 80%)` : "#0dcd06"

            if (info.view.type === "timeGridWeek") {
                return (
                    <article class="event-stream" style={{backgroundColor: bg_color}}>
                        <h3>{info.event.title}</h3>
                        <footer>
                            <img src={streamer.profile_image} alt={streamer.name} />
                            <span>{streamer.name}</span>
                        </footer>
                    </article>
                )
            }
        },

        resources: streamersResourcesURL,
        events: eventSourceURL,
    })

    calendar.render()
})
