document.addEventListener("DOMContentLoaded", () => {
    const streamersList = document.getElementById("js-streamers-list")
    const streamersModal = document.getElementById("js-add-streamers-modale")
    const streamersForm = document.getElementById("js-add-streamers-form")
    const streamersAddButton = streamersForm.querySelector("button[type=submit]")

    const csrf = document.querySelector('meta[itemprop=csrfmiddlewaretoken]').getAttribute("content")

    function updateStreamers() {
        streamersList.classList.add("is-loading")

        fetch("p/list").then(res => res.text()).then(body => {
            streamersList.innerHTML = body
        }).catch(e => {
            console.error("Unable to reload streamers", e)
        }).finally(() => {
            streamersList.classList.remove("is-loading")
        })
    }

    document.querySelectorAll('.js-add-streamers').forEach(button => {
        button.addEventListener('click', () => {
            streamersModal.classList.add("is-active")
        })
    })

    streamersForm.addEventListener("submit", ev => {
        ev.preventDefault()
        streamersAddButton.classList.add("is-loading")

        fetch("add", {
            body: new URLSearchParams(new FormData(streamersForm)),
            method: "POST"
        }).then(() => {
            streamersForm.querySelector("textarea").value = ''
        }).catch(e => {
            alert("Impossible d'ajouter les streamers, veuillez réessayer plus tard.")
            console.log("Unable to add streamers", e)
        }).finally(() => {
            streamersAddButton.classList.remove("is-loading")
            streamersModal.classList.remove("is-active")
            updateStreamers()
        })
    })

    document.querySelectorAll('.js-update-streamers').forEach(button => {
        button.addEventListener('click', ev => {
            ev.preventDefault()
            if (!confirm("Êtes-vous sûr(e) de mettre à jour les streamers depuis Twitch ? Les noms, avatars, et courtes descriptions seront écrasées avec les données de Twitch."))
                return

            button.classList.add('is-loading')
            fetch("twitch-update", {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrf
                }
            })
                .then(() => button.classList.add("is-success"))
                .catch(() => button.classList.add("is-danger"))
                .finally(() => {
                    button.classList.remove('is-loading')
                    updateStreamers()
                    setTimeout(() => button.classList.remove('is-success', 'is-danger'), 2000)
                })
        })
    })
})
