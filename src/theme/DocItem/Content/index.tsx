import React, {useState, useEffect} from 'react';
import Content from '@theme-original/DocItem/Content';
import type {Props} from '@theme/DocItem/Content';
import ReadDuration from '@site/src/components/ReadDuration';
import AIFeaturesBar from '../AIFeaturesBar';
import {useLocation} from '@docusaurus/router';

function ReadDurationHeader(props: Props) {
  const location = useLocation();
  const [pageContent, setPageContent] = useState('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);

    // Extract content from the page after it renders
    const timer = setTimeout(() => {
      const articleElement = document.querySelector('article');
      if (articleElement) {
        setPageContent(articleElement.textContent || '');
      }
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  // Don't show read duration on certain pages
  const shouldShowReadDuration = location.pathname.includes('/docs/') &&
                                !location.pathname.includes('assessments') &&
                                !location.pathname.includes('congratulations');

  useEffect(() => {
    if (!shouldShowReadDuration) return; // Don't wait for pageContent, inject when ready

    // Function to inject read duration after heading
    const injectReadDuration = () => {
      const article = document.querySelector('article');
      if (!article) return;

      // Try to find the main title:
      // 1. Custom module title (if present)
      // 2. H1 inside a header (standard Docusaurus)
      // 3. Any H1 in the article
      // 4. First H2 in the article (fallback)
      const targetH1 = article.querySelector('.module-overview h1') || 
                       article.querySelector('header h1') || 
                       article.querySelector('h1') || 
                       article.querySelector('h2');

      if (targetH1 && !targetH1.querySelector('.read-duration-wrapper')) {
        const text = targetH1.textContent?.trim();
        // basic filtering to avoid icons/empty
        if (text && !text.match(/^[\s\W]*$/)) {
                  const readDurationWrapper = document.createElement('div');
                  readDurationWrapper.className = 'read-duration-wrapper read-duration-badge';          
          const currentContent = article.textContent || pageContent || '';
          const readingTime = calculateReadingTime(currentContent);
  
          readDurationWrapper.innerHTML = `
            <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span>${readingTime.text}</span>
          `;
  
          // Apply the flexbox styling to the heading element
          const headingEl = targetH1 as HTMLElement;
          headingEl.classList.add('heading-with-duration'); // Add the new class
  
          headingEl.appendChild(readDurationWrapper);
        }
      }
    };

    // Try to inject multiple times with different delays
    injectReadDuration();
    setTimeout(injectReadDuration, 100);
    setTimeout(injectReadDuration, 300);
    setTimeout(injectReadDuration, 600);
    setTimeout(injectReadDuration, 1200);

    return () => {
      // Cleanup any existing read duration wrappers
      const existingWrappers = document.querySelectorAll('.read-duration-wrapper');
      existingWrappers.forEach(wrapper => wrapper.remove());

      // Cleanup styles
      const styles = document.querySelectorAll('style');
      styles.forEach(style => {
        if (style.textContent?.includes('read-duration-wrapper')) {
          style.remove();
        }
      });
    };
  }, [shouldShowReadDuration]);

  return (
    <>
      <AIFeaturesBar />
      <Content {...props} />
    </>
  );
}

// Helper function to calculate reading time
function calculateReadingTime(content: string) {
  const words = content.trim().split(/\s+/).filter(word => word.length > 0).length;
  const minutes = Math.ceil(words / 225);
  return {
    text: minutes === 0 ? 'Less than 1 min read' :
           minutes === 1 ? '1 min read' :
           `${minutes} min read`,
    minutes,
    words
  };
}

export default function ContentWrapper(props: Props): JSX.Element {
  return <ReadDurationHeader {...props} />;
}