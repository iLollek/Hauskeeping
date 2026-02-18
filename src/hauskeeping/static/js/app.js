/* Hauskeeping – Client-seitiges JavaScript */

// Bootstrap Tooltips initialisieren
document.addEventListener("DOMContentLoaded", function () {
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

// Service Worker registrieren (fuer Push Notifications)
if ("serviceWorker" in navigator) {
  navigator.serviceWorker
    .register(window.SW_URL)
    .then(function (registration) {
      console.log("Service Worker registriert:", registration.scope);
    })
    .catch(function (err) {
      console.log("Service Worker Registrierung fehlgeschlagen:", err);
    });
}
