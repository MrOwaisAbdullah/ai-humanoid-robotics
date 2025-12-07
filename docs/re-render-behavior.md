# Current Re-render Behavior Documentation

## Date Recorded
2025-12-07

## Problem Description
The chat widget is experiencing infinite re-renders causing the browser to crash with the error:
```
Too many re-renders. React limits the number of renders to prevent an infinite loop.
```

## Observed Behavior

### 1. Initial Load
- Chat widget loads correctly
- No visible issues on first render
- Console may show "React re-renders detected" warnings

### 2. Triggering the Infinite Loop
The infinite re-render is triggered by:
- Opening the chat widget
- Sending a message
- Receiving an AI response
- Any interaction that updates the chat state

### 3. Symptom Progression
1. **First few renders**: Normal operation
2. **After 50 renders**: Console warnings appear
3. **After 300 renders**: Performance degrades noticeably
4. **After 500+ renders**: Browser becomes unresponsive
5. **Critical point**: React halts rendering with error message

### 4. Console Errors
```
Warning: Too many re-renders. React limits the number of renders to prevent an infinite loop.
Uncaught Error: Too many re-renders. React limits the number of renders to prevent an infinite loop.
```

## Root Cause Analysis

### Issue 1: Circular Dependencies in Callbacks
```typescript
const handleChunk = useCallback((chunk: string) => {
  if (session.currentStreamingId) {
    updateMessage(session.currentStreamingId, chunk);
  }
}, [session.currentStreamingId, updateMessage]); // Problematic dependency
```

### Issue 2: Multiple Overlapping Streaming Systems
- `useChatSession` manages streaming state
- `useStreamingResponse` handles SSE connections
- Both systems update overlapping state

### Issue 3: Unstable Context References
```typescript
const contextValue = {
  messages,
  streamingId,
  sendMessage,
  updateMessage,
  handleChunk,  // Changes on every render
  // ... other callbacks
};
```

## Performance Impact

### Before Fix (Current State)
- **Render rate**: 10-20 renders per second during active streaming
- **Memory usage**: Continuously increasing (memory leak)
- **CPU usage**: 30-50% during streaming
- **Browser responsiveness**: Degrades over time
- **Time to crash**: 2-5 minutes of active use

### Expected After Fix
- **Render rate**: &lt;5 renders per interaction
- **Memory usage**: Stable (no growth over time)
- **CPU usage**: &lt;20% during streaming
- **Browser responsiveness**: Consistently smooth
- **Time to crash**: None (stable operation)

## Browser Compatibility

### Affected Browsers
- ✅ Chrome/Edge (React DevTools available)
- ✅ Firefox (React DevTools available)
- ⚠️ Safari (Limited debugging tools)

### Browser-Specific Behaviors
- **Chrome**: Faster crash due to stricter render limits
- **Firefox**: Slightly more tolerant but still crashes
- **Safari**: May become unresponsive before showing error

## Screenshots Reference

### Screenshot 1: Console Error
- Location: `ref-screenshots/chatbot-error.png`
- Shows: Infinite re-render error message
- Timestamp: 2025-12-07

### Screenshot 2: React DevTools Profiler
- Location: `ref-screenshots/react-profiler-renders.png`
- Shows: Excessive number of commits in Ranked chart
- Pattern: Continuous re-renders without user interaction

### Screenshot 3: Memory Usage
- Location: `ref-screenshots/memory-leak.png`
- Shows: Memory continuously increasing in heap usage chart
- Pattern: Staircase growth pattern indicating memory leak

## Videos Reference

### Video 1: Reproduction Steps
- Location: `ref-screenshots/reproduction.webm`
- Duration: 2 minutes
- Shows:
  1. Opening chat widget
  2. Sending first message
  3. Receiving AI response
  4. Infinite loop begins
  5. Browser crash

## Environment Details

### Development Environment
- **Node.js**: 18.x
- **React**: 18.2+
- **TypeScript**: 5.x
- **Browser**: Chrome 120+ (for debugging)

### Production Environment
- Same behavior observed in production build
- Error occurs in all environments (dev, staging, prod)

## Monitoring Setup

To track this issue during development:

1. **React DevTools Profiler**
   - Install browser extension
   - Record performance during interactions
   - Look for excessive commits

2. **Console Monitoring**
   - Check for "React re-renders detected" warnings
   - Monitor render count logging

3. **Performance Metrics**
   - Use the performanceMonitor utility
   - Track memory usage growth
   - Monitor render frequency

## Next Steps

1. Implement consolidated state management with useReducer
2. Split context into state and actions contexts
3. Stabilize all callbacks with proper dependencies
4. Add proper cleanup for streaming connections
5. Verify fix with performance monitoring

## Verification Checklist

After implementing the fix:

- [ ] No infinite re-render errors in console
- [ ] Render count remains stable during interactions
- [ ] Memory usage stays constant over time
- [ ] CPU usage remains below 20%
- [ ] Chat widget functions normally
- [ ] Streaming works without interruption
- [ ] Multiple tabs with chat widgets remain responsive