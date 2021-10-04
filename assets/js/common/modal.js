document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".modal").forEach(modal => {
        modal.querySelectorAll(".modal-close, .modal-background, .modal-close-handler").forEach(closeHandle => {
            closeHandle.addEventListener('click', () => modal.classList.remove("is-active"))
        })
    })
})
