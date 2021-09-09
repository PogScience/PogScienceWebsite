document.addEventListener("DOMContentLoaded", () => {
    const streamersModal = document.getElementById("js-add-streamers-modale")
    const streamersForm = document.getElementById("js-add-streamers-form")
    const streamersButton = streamersForm.querySelector("button[type=submit]")

    document.querySelectorAll('.js-add-streamers').forEach(button => {
        button.addEventListener('click', () => {
            streamersModal.classList.add("is-active")
        })
    })

    streamersForm.addEventListener("submit", ev => {
        ev.preventDefault()
        streamersButton.classList.add("is-loading")

        fetch("add", {
            body: new URLSearchParams(new FormData(streamersForm)),
            method: "POST"
        }).then(() => {
            streamersButton.classList.remove("is-loading")
        })
    })
})
