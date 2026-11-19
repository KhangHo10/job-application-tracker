// Client-side behavior for the Job Application Tracker (vanilla JS, no build step).

// Any <form data-confirm="..."> asks for confirmation before submitting.
// Used by every Delete button so the user sees what will cascade.
document.addEventListener("submit", function (event) {
    var message = event.target.dataset.confirm;
    if (message && !window.confirm(message)) {
        event.preventDefault();
    }
});

// Interview rounds table on the application form: "+ Add round" copies the
// row in <template id="round-template">; the x button removes its row.
function updateRoundsEmptyMessage() {
    var body = document.getElementById("rounds-body");
    var empty = document.getElementById("rounds-empty");
    if (body && empty) {
        empty.hidden = body.rows.length > 0;
    }
}

document.addEventListener("click", function (event) {
    if (event.target.closest("[data-add-round]")) {
        var template = document.getElementById("round-template");
        var body = document.getElementById("rounds-body");
        body.appendChild(template.content.cloneNode(true));
        body.rows[body.rows.length - 1].querySelector("input").focus();
        updateRoundsEmptyMessage();
        return;
    }
    var removeButton = event.target.closest("[data-remove-round]");
    if (removeButton) {
        removeButton.closest("tr").remove();
        updateRoundsEmptyMessage();
    }
});

// <input type="checkbox" data-toggle-fieldset="#id"> shows/enables that fieldset
// while checked. A disabled fieldset's fields are not validated or submitted.
document.addEventListener("change", function (event) {
    var selector = event.target.dataset && event.target.dataset.toggleFieldset;
    if (selector) {
        var fieldset = document.querySelector(selector);
        fieldset.disabled = !event.target.checked;
        fieldset.hidden = !event.target.checked;
    }
});
