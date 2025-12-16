/**
 * Content extraction utility for personalization feature.
 *
 * This module provides functions to extract meaningful content
 * from the current page or given selectors for personalization.
 */

export interface ExtractionOptions {
  selector?: string;
  excludeSelectors?: string[];
  includeImages?: boolean;
  includeCode?: boolean;
  includeMetadata?: boolean;
  maxLength?: number;
  minWordCount?: number;
}

export interface ExtractedContent {
  content: string;
  title?: string;
  wordCount: number;
  sourceUrl: string;
  metadata: {
    extractionMethod: string;
    elementCount: number;
    hasCode: boolean;
    hasImages: boolean;
    estimatedReadTime: number;
  };
}

/**
 * Default selectors for Docusaurus documentation sites
 */
const DEFAULT_CONTENT_SELECTORS = [
  'article',
  '[class*="markdown"]',
  '[class*="content"]',
  'main',
  '.theme-doc-markdown',
  '.markdown'
];

/**
 * Default selectors to exclude from content extraction
 */
const DEFAULT_EXCLUDE_SELECTORS = [
  'nav',
  'header',
  'footer',
  '.pagination',
  '.table-of-contents',
  '.breadcrumb',
  '.sidebar',
  'script',
  'style',
  'noscript',
  '[class*="nav"]',
  '[class*="menu"]',
  '[class*="toc"]',
  '[class*="sidebar"]',
  '[class*="footer"]',
  '[class*="header"]',
  '[class*="toolbar"]',
  '[class*="breadcrumb"]',
  '[class*="pagination"]',
  '.ad',
  '.advertisement',
  '[data-ad]',
  '.social-share',
  '.comments',
  '.theme-doc-sidebar',
  '.theme-doc-toc',
  '.theme-doc-breadcrumbs',
  '.theme-doc-footer',
  '.theme-doc-pagination',
  '.menu',
  '.navbar',
  '.btn',
  '.button',
  '.ai-features-bar',
  '.ai-feature-btn',
  '.theme-edit-this-page',
  '.last-updated'
];

/**
 * Extract content from the current page
 */
export const extractCurrentPageContent = (
  options: ExtractionOptions = {}
): ExtractedContent => {
  const {
    selector,
    excludeSelectors = [],
    includeImages = false,
    includeCode = true,
    includeMetadata = false,
    maxLength = 50000,
    minWordCount = 50
  } = options;

  // Try to find the main content element
  const contentElement = findContentElement(selector);
  if (!contentElement) {
    throw new Error('Could not find content element on the page');
  }

  // Clone the element to avoid modifying the DOM
  const clonedElement = contentElement.cloneNode(true) as Element;

  // Remove excluded elements
  const elementsToExclude = [
    ...DEFAULT_EXCLUDE_SELECTORS,
    ...excludeSelectors
  ];

  elementsToExclude.forEach(selector => {
    const elements = clonedElement.querySelectorAll(selector);
    elements.forEach(el => el.remove());
  });

  // Extract text content
  const content = extractTextContent(clonedElement, {
    includeCode,
    includeImages,
    maxLength
  });

  // Calculate metrics
  const wordCount = countWords(content);

  // Validate minimum word count
  if (wordCount < minWordCount) {
    throw new Error(`Content too short: ${wordCount} words (minimum ${minWordCount} required)`);
  }

  // Extract metadata
  const metadata = extractMetadata(clonedElement, {
    hasCode: includeCode && containsCode(clonedElement),
    hasImages: includeImages && containsImages(clonedElement)
  });

  return {
    content,
    title: extractTitle(),
    wordCount,
    sourceUrl: window.location.href,
    metadata
  };
};

/**
 * Find the main content element
 */
function findContentElement(customSelector?: string): Element | null {
  // If custom selector is provided, try it first
  if (customSelector) {
    const element = document.querySelector(customSelector);
    if (element) {
      return element;
    }
  }

  // Try default selectors in order of preference
  for (const selector of DEFAULT_CONTENT_SELECTORS) {
    const element = document.querySelector(selector);
    if (element) {
      return element;
    }
  }

  // Fallback: try to find the element with the most text
  const allElements = document.querySelectorAll('*');
  let bestElement: Element | null = null;
  let maxTextLength = 0;

  allElements.forEach(el => {
    // Skip certain element types
    if (['SCRIPT', 'STYLE', 'NAV', 'HEADER', 'FOOTER'].includes(el.tagName)) {
      return;
    }

    const textLength = el.textContent?.length || 0;
    if (textLength > maxTextLength) {
      maxTextLength = textLength;
      bestElement = el;
    }
  });

  return bestElement;
}

/**
 * Extract clean text content from an element
 */
function extractTextContent(
  element: Element,
  options: {
    includeCode: boolean;
    includeImages: boolean;
    maxLength: number;
  }
): string {
  const { includeCode, includeImages, maxLength } = options;

  let content = '';

  // Handle different element types
  if (element.tagName === 'CODE' || element.tagName === 'PRE') {
    if (includeCode) {
      content = element.textContent || '';
    }
  } else if (element.tagName === 'IMG') {
    if (includeImages) {
      const alt = element.getAttribute('alt');
      const title = element.getAttribute('title');
      content = `[Image: ${alt || title || 'No description'}]`;
    }
  } else {
    // Process child elements
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
      {
        acceptNode: (node) => {
          if (node.nodeType === Node.TEXT_NODE) {
            // Accept text nodes
            return NodeFilter.FILTER_ACCEPT;
          } else if (node.nodeType === Node.ELEMENT_NODE) {
            const el = node as Element;
            if (el.tagName === 'CODE' || el.tagName === 'PRE') {
              return includeCode ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
            } else if (el.tagName === 'IMG') {
              return includeImages ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
            } else {
              return NodeFilter.FILTER_ACCEPT;
            }
          }
          return NodeFilter.FILTER_REJECT;
        }
      }
    );

    const textParts: string[] = [];
    let currentParagraph = '';

    while (walker.nextNode()) {
      const node = walker.currentNode;

      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent?.trim() || '';
        if (text) {
          currentParagraph += text + ' ';
        }
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        const el = node as Element;

        if (el.tagName === 'CODE' || el.tagName === 'PRE') {
          if (includeCode) {
            const code = el.textContent?.trim() || '';
            if (currentParagraph.trim()) {
              textParts.push(currentParagraph.trim());
              currentParagraph = '';
            }
            textParts.push(`\n[code]\n${code}\n[/code]\n`);
          }
        } else if (el.tagName === 'IMG') {
          if (includeImages) {
            const alt = el.getAttribute('alt');
            const title = el.getAttribute('title');
            const imgText = `[Image: ${alt || title || 'No description'}]`;
            if (currentParagraph.trim()) {
              textParts.push(currentParagraph.trim());
              currentParagraph = '';
            }
            textParts.push(imgText);
          }
        } else if (['P', 'DIV', 'SECTION', 'ARTICLE'].includes(el.tagName)) {
          // Add paragraph break
          if (currentParagraph.trim()) {
            textParts.push(currentParagraph.trim());
            currentParagraph = '';
          }
        } else if (['BR', 'HR'].includes(el.tagName)) {
          // Add line break
          if (currentParagraph.trim()) {
            textParts.push(currentParagraph.trim());
            currentParagraph = '';
          }
          textParts.push('');
        }
      }
    }

    // Add any remaining paragraph
    if (currentParagraph.trim()) {
      textParts.push(currentParagraph.trim());
    }

    content = textParts.join('\n\n');
  }

  // Clean up whitespace and remove UI patterns
  content = content
    .replace(/\n{3,}/g, '\n\n') // Remove excessive line breaks
    .replace(/[ \t]{2,}/g, ' ') // Remove excessive spaces
    .split('\n') // Split into lines for filtering
    .filter(line => {
      const trimmedLine = line.trim();
      const lowerLine = trimmedLine.toLowerCase();

      // Skip patterns that indicate UI elements
      const skipPatterns = [
        'personalize', 'translate', 'read aloud', 'min read', 'minute read',
        'edit this page', 'last updated', 'previous', 'next',
        'welcome on this page', 'ai features', 'share', 'copy link',
        'table of contents', 'on this page', 'breadcrumbs',
        'facebook', 'twitter', 'linkedin', 'github'
      ];

      const hasSkipPattern = skipPatterns.some(pattern => lowerLine.includes(pattern));
      const isTooShort = trimmedLine.length < 3;
      const isJustNumber = /^\d+$/.test(trimmedLine);

      return !hasSkipPattern && !isTooShort && !isJustNumber;
    })
    .join('\n')
    .replace(/\b(min read|edit this page|last updated|ai features)\b/gi, '') // Clean up any remaining patterns
    .trim();

  // Enforce maximum length
  if (maxLength && content.length > maxLength) {
    // Try to cut at a sentence boundary
    const truncated = content.substring(0, maxLength);
    const lastSentenceEnd = Math.max(
      truncated.lastIndexOf('.'),
      truncated.lastIndexOf('!'),
      truncated.lastIndexOf('?')
    );

    if (lastSentenceEnd > maxLength * 0.8) {
      content = truncated.substring(0, lastSentenceEnd + 1);
    } else {
      content = truncated + '...';
    }
  }

  return content;
}

/**
 * Extract page title
 */
function extractTitle(): string {
  // Try different title sources
  const titleSelectors = [
    'h1',
    '[class*="title"]',
    '.theme-doc-title',
    'title'
  ];

  for (const selector of titleSelectors) {
    const element = document.querySelector(selector);
    if (element) {
      const text = element.textContent?.trim();
      if (text && text.length > 0 && text.length < 200) {
        return text;
      }
    }
  }

  // Fallback to document title
  return document.title || 'Untitled Document';
}

/**
 * Extract metadata about the content
 */
function extractMetadata(element: Element, extraData: any) {
  return {
    extractionMethod: 'dom',
    elementCount: element.querySelectorAll('*').length,
    ...extraData,
    estimatedReadTime: Math.max(1, Math.round(countWords(element.textContent || '') / 200))
  };
}

/**
 * Count words in text
 */
function countWords(text: string): number {
  return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

/**
 * Check if element contains code
 */
function containsCode(element: Element): boolean {
  return !!element.querySelector('code, pre, [class*="code"], [class*="highlight"]');
}

/**
 * Check if element contains images
 */
function containsImages(element: Element): boolean {
  return !!element.querySelector('img, [class*="image"], [class*="figure"]');
}

/**
 * Validate content for personalization
 */
export const validateContent = (content: string): {
  valid: boolean;
  errors: string[];
  warnings: string[];
} => {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check minimum length
  const wordCount = countWords(content);
  if (wordCount < 50) {
    errors.push('Content too short: minimum 50 words required');
  }

  // Check maximum length
  if (wordCount > 10000) {
    warnings.push('Content very long: personalization may take longer');
  }

  // Check for meaningful content
  if (!containsMeaningfulContent(content)) {
    errors.push('Content appears to be mostly code or non-technical text');
  }

  // Check for repetitive content
  if (isRepetitiveContent(content)) {
    warnings.push('Content appears repetitive - personalization quality may be reduced');
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
};

/**
 * Check if content contains meaningful technical content
 */
function containsMeaningfulContent(text: string): boolean {
  const technicalTerms = [
    'algorithm', 'data', 'system', 'process', 'method', 'function',
    'implementation', 'architecture', 'design', 'model', 'structure',
    'robotics', 'ai', 'machine learning', 'computer vision', 'sensor'
  ];

  const lowerText = text.toLowerCase();
  const foundTerms = technicalTerms.filter(term => lowerText.includes(term));

  // If less than 20% of technical terms are found, might not be technical content
  return foundTerms.length > technicalTerms.length * 0.2;
}

/**
 * Check if content is repetitive
 */
function isRepetitiveContent(text: string): boolean {
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
  if (sentences.length < 3) return false;

  // Check for repeated sentences
  const uniqueSentences = new Set(sentences.map(s => s.trim().toLowerCase()));
  const repetitionRatio = 1 - (uniqueSentences.size / sentences.length);

  return repetitionRatio > 0.3; // More than 30% repetition
}

/**
 * Extract content from selected text
 */
export const extractSelectedText = (): string | null => {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed) {
    return null;
  }

  const selectedText = selection.toString().trim();

  // Filter out UI elements and noise from selected text
  const lines = selectedText.split('\n').filter(line => {
    const trimmedLine = line.trim();
    const lowerLine = trimmedLine.toLowerCase();

    // Skip if line contains UI text patterns
    const skipPatterns = [
      'personalize', 'translate', 'read aloud', 'min read', 'minute read',
      'edit this page', 'last updated', 'previous', 'next',
      'welcome on this page', 'ai features', 'share', 'copy link',
      'table of contents', 'on this page', 'breadcrumbs',
      'facebook', 'twitter', 'linkedin', 'github'
    ];

    const hasSkipPattern = skipPatterns.some(pattern => lowerLine.includes(pattern));

    // Skip if line is too short (likely UI debris)
    const isTooShort = trimmedLine.length < 3;

    // Skip if line is just a number or single character
    const isJustNumber = /^\d+$/.test(trimmedLine);

    return !hasSkipPattern && !isTooShort && !isJustNumber;
  });

  const cleanedText = lines.join('\n');

  // Final cleanup of common UI patterns
  return cleanedText
    .replace(/\b(min read|edit this page|last updated|ai features)\b/gi, '')
    .replace(/\s+/g, ' ')
    .trim() || null;
};

/**
 * Get selection context around the selected text
 */
export const getSelectionContext = (
  beforeWords: number = 50,
  afterWords: number = 50
): {
  before: string;
  selected: string;
  after: string;
} => {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed) {
    return { before: '', selected: '', after: '' };
  }

  const range = selection.getRangeAt(0);
  const container = range.commonAncestorContainer;
  const fullText = container.textContent || '';

  const startOffset = range.startOffset;
  const endOffset = range.endOffset;
  const selectedText = selection.toString();

  // Extract words before and after selection
  const beforeText = extractWordsAround(fullText, startOffset, beforeWords, true);
  const afterText = extractWordsAround(fullText, endOffset, afterWords, false);

  return {
    before: beforeText,
    selected: selectedText,
    after: afterText
  };
};

/**
 * Extract words around a position in text
 */
function extractWordsAround(
  text: string,
  position: number,
  wordCount: number,
  before: boolean
): string {
  const words = text.split(/\s+/);
  let currentPos = 0;
  let targetPos = 0;

  // Find the word at the position
  for (let i = 0; i < words.length; i++) {
    if (currentPos >= position) {
      targetPos = i;
      break;
    }
    currentPos += words[i].length + 1; // +1 for space
  }

  // Extract words before or after
  if (before) {
    const start = Math.max(0, targetPos - wordCount);
    return words.slice(start, targetPos).join(' ');
  } else {
    const end = Math.min(words.length, targetPos + wordCount);
    return words.slice(targetPos, end).join(' ');
  }
}