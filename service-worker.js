self.addEventListener("install", event => {
    console.log("DSMARKET installed");
    self.skipWaiting();
});

self.addEventListener("activate", event => {
    console.log("DSMARKET active");
});

self.addEventListener("fetch", event => {
    event.respondWith(fetch(event.request));
});