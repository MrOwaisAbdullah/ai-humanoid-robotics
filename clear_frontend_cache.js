// Script to clear all frontend cache
// Run this in the browser console to clear cached translations

console.log("Clearing frontend cache...");

// Clear localStorage
if (typeof window !== 'undefined' && window.localStorage) {
    // Get all keys in localStorage
    const keys = Object.keys(localStorage);
    let clearedCount = 0;

    // Clear all cache-related entries
    keys.forEach(key => {
        if (key.includes('app_cache') ||
            key.includes('translation') ||
            key.includes('translate') ||
            key.includes('ur') ||
            key.includes(' cached')) {
            localStorage.removeItem(key);
            clearedCount++;
            console.log(`Cleared: ${key}`);
        }
    });

    console.log(`Cleared ${clearedCount} localStorage entries`);
}

// Clear sessionStorage
if (typeof window !== 'undefined' && window.sessionStorage) {
    const sessionKeys = Object.keys(sessionStorage);
    let clearedSessionCount = 0;

    sessionKeys.forEach(key => {
        if (key.includes('app_cache') ||
            key.includes('translation') ||
            key.includes('translate') ||
            key.includes('ur') ||
            key.includes(' cached')) {
            sessionStorage.removeItem(key);
            clearedSessionCount++;
            console.log(`Cleared session: ${key}`);
        }
    });

    console.log(`Cleared ${clearedSessionCount} sessionStorage entries`);
}

// Clear any service worker cache
if ('serviceWorker' in navigator && 'caches' in window) {
    caches.keys().then(cacheNames => {
        return Promise.all(
            cacheNames.map(cacheName => {
                console.log(`Deleting cache: ${cacheName}`);
                return caches.delete(cacheName);
            })
        );
    }).then(() => {
        console.log('All caches cleared');
    });
}

console.log("Frontend cache cleared! Please refresh the page.");