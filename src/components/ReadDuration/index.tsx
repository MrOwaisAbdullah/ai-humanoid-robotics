import React from 'react';
import { calculateReadingTime, extractTextContent } from '../../utils/readingTime';

interface ReadDurationProps {
  content: string;
  className?: string;
  wordsPerMinute?: number;
  showWordCount?: boolean;
}

/**
 * ReadDuration component - displays estimated reading time for content
 *
 * @param content - Text content to analyze for reading time calculation
 * @param className - Additional CSS classes for styling
 * @param wordsPerMinute - Reading speed for calculation (default: 225 WPM)
 * @param showWordCount - Whether to display word count alongside reading time
 */
export function ReadDuration({
  content,
  className = '',
  wordsPerMinute = 225,
  showWordCount = false,
}: ReadDurationProps): React.ReactElement {
  // Extract plain text from content
  const textContent = extractTextContent(content);

  // Calculate reading time
  const readingTime = calculateReadingTime(textContent, wordsPerMinute);

  return (
    <div className={`read-duration ${className}`}>
      <span
        className="inline-flex items-center gap-1 text-sm text-zinc-500 dark:text-zinc-400 font-medium"
        title={`Approximately ${readingTime.words} words`}
      >
        {/* Clock icon */}
        <svg
          className="w-3 h-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>

        {/* Reading time text */}
        <span>{readingTime.text}</span>

        {/* Optional word count */}
        {showWordCount && (
          <span className="text-xs opacity-60 ml-1">
            ({readingTime.words.toLocaleString()} words)
          </span>
        )}
      </span>
    </div>
  );
}

export default ReadDuration;