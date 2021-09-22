let csrf = null

export default (url, params) => {
    if (csrf === null) {
        csrf = document.querySelector('meta[itemprop=csrfmiddlewaretoken]').getAttribute("content")
    }

    const defaultHeaders = {
        'X-CSRFToken': csrf,
        'X-Requested-With': 'XMLHttpRequest',
    }

    params = params || {}
    params.headers = {...defaultHeaders, ...params.headers || {}}

    return fetch(url, params)
}
