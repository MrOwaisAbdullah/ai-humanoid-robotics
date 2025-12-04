import React from 'react';
import DocItem from '@theme-original/DocItem';
import type {Props} from '@theme/DocItem';

// Simple Toast implementation for the "Coming Soon" feature
const showToast = (message: string) => {
  const toast = document.createElement('div');
  toast.className = 'fixed bottom-5 right-5 bg-zinc-900 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in-up border border-zinc-800';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3000);
};

function ActionButtonsHeader() {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);

    // Function to inject AI Features after breadcrumbs
    const injectAIFeatures = () => {
      // Find breadcrumb container or title container
      const breadcrumbsElement = document.querySelector('.breadcrumbs') ||
                              document.querySelector('.theme-doc-breadcrumbs') ||
                              document.querySelector('.theme-doc-markdown h1')?.parentElement;

      if (breadcrumbsElement && !document.querySelector('.ai-features-bar')) {
        const aiFeaturesBar = document.createElement('div');
        aiFeaturesBar.className = 'ai-features-bar glass-bar'; // Use new glass-bar class
        
        // Remove inline styles for layout that are now handled by classes, but keep structural ones
        aiFeaturesBar.style.cssText = `
          border-radius: 10px;
          padding: 12px 20px;
          margin: 24px 0; /* Added top margin for spacing */
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 16px;
          position: sticky;
          top: 20px;
          z-index: 100;
          transition: all 0.3s ease;
        `;

        aiFeaturesBar.innerHTML = `
          <div style="color: var(--color-fg-muted); font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px;">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
            AI Features
          </div>
          <div style="display: flex; gap: 12px; align-items: center;">
            <button
              class="button button--primary button--sm"
              style="display: flex; align-items: center; gap: 6px;"
              onclick="window.showToast('Personalization coming soon!')"
            >
              <span style="font-size: 16px;">✨</span>
              Personalize
            </button>
            <button
              class="button button--secondary button--sm"
              style="display: flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.1);"
              onclick="window.showToast('Urdu translation coming soon!')"
            >
              <span style="font-size: 16px;">🌐</span>
              Translate to Urdu
            </button>
          </div>
        `;

        // Insert after breadcrumbs or before title
        const targetElement = breadcrumbsElement;
        targetElement.parentNode?.insertBefore(aiFeaturesBar, targetElement.nextSibling);

        // Add toast function to window if it doesn't exist
        if (!window.showToast) {
          window.showToast = function(message: string) {
            const toast = document.createElement('div');
            toast.className = 'fixed bottom-5 right-5 bg-zinc-900 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in-up border border-zinc-800';
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => {
              toast.remove();
            }, 3000);
          };
        }
      }
    };

    // Try to inject after component mount
    injectAIFeatures();
    setTimeout(injectAIFeatures, 100);
    setTimeout(injectAIFeatures, 300);

    return () => {
      // Cleanup
      const aiFeaturesBar = document.querySelector('.ai-features-bar');
      if (aiFeaturesBar) {
        aiFeaturesBar.remove();
      }
    };
  }, []);

  return null; // This component now handles injection via useEffect
}

// Add global type for window.showToast
declare global {
  interface Window {
    showToast?: (message: string) => void;
  }
}

export default function DocItemWrapper(props: Props): JSX.Element {
  return (
    <>
      <ActionButtonsHeader />
      <DocItem {...props} />
    </>
  );
}