// Client-side behavior for the Job Application Tracker (vanilla JS, no build step).

// Any <form data-confirm="..."> asks for confirmation before submitting.
// Used by every Delete button so the user sees what will cascade.
document.addEventListener("submit", function (event) {
    var message = event.target.dataset.confirm;
    if (message && !window.confirm(message)) {
        event.preventDefault();
    }
});
