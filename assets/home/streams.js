import fetch from "../common/fetch"

document.addEventListener("DOMContentLoaded", () => {
    const streamsContainer = document.getElementById("js-home-live-and-upcoming")
    if (!streamsContainer) return

    const streamsLiveURL = streamsContainer.getAttribute("data-content-url")

    function updateStreams() {
        fetch(streamsLiveURL).then(r => r.text()).then(content => streamsContainer.innerHTML = content)
    }

    setInterval(updateStreams, 30000)
    updateStreams()
})
