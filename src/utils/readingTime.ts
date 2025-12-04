/**
 * Reading time utility for estimating content consumption duration
 * Based on average reading speed of 225 words per minute
 */

export interface ReadingTimeResult {
  minutes: number;
  words: number;
  text: string;
}

/**
 * Calculate estimated reading time for text content
 * @param content - Text content to analyze
 * @param wordsPerMinute - Reading speed (default: 225 WPM)
 * @returns Reading time information
 */
export function calculateReadingTime(
  content: string,
  wordsPerMinute: number = 225
): ReadingTimeResult {
  // Remove HTML tags and decode HTML entities
  const cleanContent = content
    .replace(/<[^>]*>/g, '') // Remove HTML tags
    .replace(/&nbsp;/g, ' ') // Replace non-breaking spaces
    .replace(/&amp;/g, '&') // Replace HTML entities
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");

  // Split into words and count
  const words = cleanContent
    .trim()
    .split(/\s+/)
    .filter(word => word.length > 0).length;

  // Calculate reading time
  const minutes = Math.ceil(words / wordsPerMinute);

  // Generate human-readable text
  let text = '';
  if (minutes === 0) {
    text = 'Less than 1 min read';
  } else if (minutes === 1) {
    text = '1 min read';
  } else {
    text = `${minutes} min read`;
  }

  return {
    minutes,
    words,
    text,
  };
}

/**
 * Extract text content from MDX/HTML string
 * @param content - MDX or HTML content
 * @returns Plain text content
 */
export function extractTextContent(content: string): string {
  return content
    .replace(/```[\s\S]*?```/g, '') // Remove code blocks
    .replace(/`[^`]*`/g, '') // Remove inline code
    .replace(/!\[.*?\]\(.*?\)/g, '') // Remove images
    .replace(/\[.*?\]\(.*?\)/g, '$1') // Convert links to text
    .replace(/#{1,6}\s+/g, '') // Remove markdown headers
    .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markup
    .replace(/\*(.*?)\*/g, '$1') // Remove italic markup
    .replace(/_(.*?)_/g, '$1') // Remove underline markup
    .replace(/`[^`]*`/g, '') // Remove inline code (again)
    .replace(/<[^>]*>/g, '') // Remove any remaining HTML tags
    .trim();
}