import { useState, useEffect } from 'react';

/**
 * Text selection detection hook
 * Captures user text selections from article content
 */
export function useTextSelection() {
  const [selectedText, setSelectedText] = useState<string | null>(null);

  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();

      // Only capture meaningful selections from content
      if (text && text.length > 10) {
        const range = selection?.getRangeAt(0);
        const container = range?.commonAncestorContainer;

        // Check if selection is from article content (not UI)
        // In Docusaurus, content is usually in main or article
        const isFromContent =
          container?.parentElement?.closest('article') !== null ||
          container?.parentElement?.closest('main') !== null;

        if (isFromContent) {
          setSelectedText(text);
        }
      }
    };

    // Debounce to avoid excessive updates
    let timeoutId: NodeJS.Timeout;
    const debouncedHandler = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(handleSelection, 300);
    };

    document.addEventListener('mouseup', debouncedHandler);
    document.addEventListener('touchend', debouncedHandler);

    return () => {
      document.removeEventListener('mouseup', debouncedHandler);
      document.removeEventListener('touchend', debouncedHandler);
      clearTimeout(timeoutId);
    };
  }, []);

  const clearSelection = () => setSelectedText(null);

  return { selectedText, clearSelection };
}