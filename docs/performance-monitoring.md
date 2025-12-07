# Performance Monitoring Guide

## Required Tools

### React DevTools Profiler
Install the React DevTools browser extension:
- Chrome Web Store: https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbfjdgkbhgigm/
- Firefox Add-ons: https://addons.mozilla.org/en-US/firefox/addon/react-developer-tools/
- Edge Add-ons: Available in Microsoft Store

### Using the Profiler

1. Open the chat widget page
2. Open React DevTools (F12 → Profiler tab)
3. Record performance while interacting with the chat
4. Look for:
   - Excessive re-renders (many bars in "Ranked")
   - Component mounting/unmounting patterns
   - Long commit times

## Baseline Measurements

Before implementing fixes:
1. Open chat widget → Count renders
2. Send 5 messages → Record render count
3. Check memory usage in DevTools Memory tab
4. Document baseline for comparison

## After Fix Validation

After implementing the infinite re-render fix:
1. Same operations should show dramatically fewer renders
2. Memory usage should remain stable
3. No "React re-renders detected" warnings in console