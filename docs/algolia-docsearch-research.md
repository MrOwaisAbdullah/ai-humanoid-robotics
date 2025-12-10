# Algolia DocSearch Research Report for Docusaurus Implementation

*Research conducted: December 2025*

## Executive Summary

Algolia DocSearch is a free, hosted search solution specifically designed for technical documentation. However, as of December 2024, **DocSearch applications are currently paused** and remain paused in early 2025. This report covers integration details, multilingual support considerations, and alternatives for your educational book website with Urdu-English content.

## 1. Integration with Docusaurus 3.x

### 1.1 Configuration Setup

To integrate Algolia DocSearch with Docusaurus 3.x, add the following configuration to your `docusaurus.config.js`:

```javascript
export default {
  // ...
  themeConfig: {
    // ...
    algolia: {
      // The application ID provided by Algolia
      appId: 'YOUR_APP_ID',
      // Public API key: it is safe to commit it
      apiKey: 'YOUR_SEARCH_API_KEY',
      indexName: 'YOUR_INDEX_NAME',

      // Optional: see doc section below
      contextualSearch: true,

      // Optional: Specify domains where the navigation should occur through window.location instead on history.push
      externalUrlRegex: 'external\\.com|domain\\.com',

      // Optional: Replace parts of the item URLs from Algolia
      replaceSearchResultPathname: {
        from: '/docs/', // or as RegExp: /\/docs\//
        to: '/',
      },

      // Optional: Algolia search parameters
      searchParameters: {},

      // Optional: path for search page that enabled by default (`false` to disable it)
      searchPagePath: 'search',

      // Optional: whether the insights feature is enabled or not on Docsearch (`false` by default)
      insights: false,
    },
  },
};
```

### 1.2 Theme Installation

If you're not using `@docusaurus/preset-classic`, install the Algolia theme:

```bash
# Using npm
npm install --save @docusaurus/theme-search-algolia

# Using yarn
yarn add @docusaurus/theme-search-algolia

# Using pnpm
pnpm add @docusaurus/theme-search-algolia
```

### 1.3 Custom Styling

You can style the DocSearch component using CSS variables:

```css
[data-theme='light'] .DocSearch {
  --docsearch-primary-color: var(--ifm-color-primary);
  --docsearch-text-color: var(--ifm-font-color-base);
  --docsearch-muted-color: var(--ifm-color-secondary-darkest);
  --docsearch-container-background: rgba(94, 100, 112, 0.7);
  /* Modal */
  --docsearch-modal-background: var(--ifm-color-secondary-lighter);
  /* Search box */
  --docsearch-searchbox-background: var(--ifm-color-secondary);
  --docsearch-searchbox-focus-background: var(--ifm-color-white);
  /* Hit */
  --docsearch-hit-color: var(--ifm-font-color-base);
  --docsearch-hit-active-color: var(--ifm-color-white);
  --docsearch-hit-background: var(--ifm-color-white);
  /* Footer */
  --docsearch-footer-background: var(--ifm-color-white);
}

[data-theme='dark'] .DocSearch {
  --docsearch-text-color: var(--ifm-font-color-base);
  --docsearch-muted-color: var(--ifm-color-secondary-darkest);
  --docsearch-container-background: rgba(47, 55, 69, 0.7);
  /* Modal */
  --docsearch-modal-background: var(--ifm-background-color);
  /* Search box */
  --docsearch-searchbox-background: var(--ifm-background-color);
  --docsearch-searchbox-focus-background: var(--ifm-color-black);
  /* Hit */
  --docsearch-hit-color: var(--ifm-font-color-base);
  --docsearch-hit-active-color: var(--ifm-color-white);
  --docsearch-hit-background: var(--ifm-color-emphasis-100);
  /* Footer */
  --docsearch-footer-background: var(--ifm-color-surface-color);
}
```

## 2. Multilingual Support (English/Urdu)

### 2.1 Current Capabilities

Algolia has enhanced multilingual support that can handle:

- **Bidirectional text rendering** (RTL for Urdu, LTR for English)
- **Mixed-language content** within the same document
- **Language detection** at the document and content block level
- **Urdu text processing** with appropriate tokenization for Arabic script
- **Context-aware ranking** based on user language preferences

### 2.2 Recommended Configuration for Urdu-English Mixed Content

For optimal multilingual search, structure your content to clearly identify language sections:

```javascript
// Example content structure for mixed language
{
  "title": "آپ کی کتاب - Your Book",
  "content": {
    "ur": "یہاں اردو متن ہے",
    "en": "English text here",
    "mixed": "یہ Urdu text میں English words ہیں"
  },
  "language": "ur-en"  // Custom field to indicate mixed content
}
```

### 2.3 Index Configuration Best Practices

1. **Enable language detection** in Algolia dashboard
2. **Use a single multilingual index** rather than separate indices
3. **Configure appropriate searchable attributes** for each language
4. **Set up custom ranking** to prioritize content based on user language preference
5. **Implement language-specific query processing** in your search interface

### 2.4 Handling Transliterated Terms

For English technical terms transliterated into Urdu script:

- **Index both versions**: Original English and transliterated Urdu
- **Use synonyms** to map transliterations back to original terms
- **Configure custom ranking** to prioritize original terminology
- **Consider user search patterns** to understand preferred search language

## 3. Pricing and Limits

### 3.1 DocSearch Free Tier

- **100% FREE** for qualifying technical documentation and educational content
- **No limits** on number of queries or indexed pages
- **No hosting costs** - fully managed by Algolia
- **99.99% uptime** guarantee
- **Sub-20ms response time** globally

### 3.2 Eligibility Requirements

Your website must:
- Be a **technical documentation or educational book**
- Be **publicly accessible** (no authentication required)
- Be **production ready** with substantial content
- Be **owned** by you (you must have permissions to add JavaScript)

### 3.3 Important Note: Application Status

**As of December 2024, DocSearch applications are PAUSED** and remain paused in early 2025. The service is expected to reopen for new applications at some point in 2025.

## 4. Implementation Timeline

### 4.1 When Applications Are Open

1. **Application Submission**: Submit your documentation site for review
2. **Review Process**: Manual review by Algolia team (can take 1-2 weeks)
3. **Configuration Setup**: Algolia team sets up your search index
4. **Implementation**: Add provided JavaScript to your site
5. **Testing and Go-live**: Final testing and deployment

**Total timeline**: 2 weeks to 2+ months (based on historical data)

### 4.2 Current Situation (2025)

Since applications are paused, you'll need to consider alternatives (see Section 6).

## 5. Contextual Search Configuration

### 5.1 Enabling Contextual Search

```javascript
// In docusaurus.config.js
algolia: {
  // ... other config
  contextualSearch: true,
  searchParameters: {
    // Boosts results based on page hierarchy
    'facetFilters': ['language:${language}', 'version:${version}'],
    // Custom ranking for educational content
    'ranking': [
      'typo',
      'geo',
      'words',
      'filters',
      'proximity',
      'attribute',
      'exact',
      'custom'
    ],
    'customRanking': [
      'desc(book_order)',
      'desc(page_depth)',
      'desc(content_relevance)'
    ]
  }
}
```

### 5.2 Best Practices for Educational Content

1. **Section-based indexing**: Index by chapters, sections, and subsections
2. **Content type filtering**: Distinguish between definitions, examples, exercises
3. **Progress tracking**: Allow users to see their reading progress in search
4. **Cross-references**: Link related concepts across different sections

## 6. Alternatives to DocSearch (Given Current Pause)

### 6.1 PageFind (Recommended for Static Sites)

**Pros:**
- Zero configuration required
- Fully static (no server needed)
- Excellent performance
- Works perfectly with Docusaurus
- Supports multilingual content

**Implementation:**
```bash
npm install pagefind
```

```javascript
// In docusaurus.config.js
const pagefind = require('pagefind');

// Add to your build process
```

### 6.2 Typesense with DocSearch Scraper

**Pros:**
- Open source and self-hosted
- DocSearch-compatible scraper available
- Excellent multilingual support
- Fast and relevant search

**Implementation:**
1. Deploy Typesense server
2. Use the open-source scraper: https://github.com/typesense/docsearch-scraper
3. Configure with your Docusaurus build

### 6.3 Meilisearch Documentation Search

**Pros:**
- Lightweight and fast
- Good multilingual support
- Easy to set up
- RESTful API

**Implementation:**
1. Deploy Meilisearch
2. Use: https://github.com/meilisearch/documentation-search
3. Integrate with Docusaurus

### 6.4 Algolia InstantSearch (Self-Hosted Index)

If you want Algolia quality but immediate implementation:

```javascript
// Install InstantSearch
npm install algoliasearch instantsearch.js react-instantsearch

// Configure in your Docusaurus site
import algoliasearch from 'algoliasearch/lite';
import { InstantSearch } from 'react-instantsearch';

const searchClient = algoliasearch('YOUR_APP_ID', 'YOUR_API_KEY');
```

## 7. Implementation Effort Comparison

| Solution | Implementation Time | Maintenance | Cost | Multilingual Support |
|----------|-------------------|-------------|------|---------------------|
| DocSearch (when available) | 1-2 weeks | None | Free | Excellent |
| PageFind | 1-2 days | Minimal | Free | Good |
| Typesense + Scraper | 1-2 weeks | Medium | Low | Excellent |
| Meilisearch | 1 week | Low | Free | Good |
| InstantSearch (self-index) | 2-3 weeks | High | Paid | Excellent |

## 8. Recommendations for Your Educational Book

### 8.1 Short-term Solution (Immediate Implementation)

Given the current pause on DocSearch applications, I recommend:

1. **PageFind** for immediate search implementation
   - Fastest setup (1-2 days)
   - No server requirements
   - Good multilingual support for Urdu-English content

### 8.2 Long-term Solution

1. **Apply for DocSearch** when applications reopen
   - Best search quality
   - Zero maintenance
   - Excellent multilingual features

2. **Or implement Typesense** if you need more features than PageFind offers
   - DocSearch-compatible scraper available
   - Full control over ranking and features
   - Excellent Urdu text processing

### 8.3 Implementation Steps

**For PageFind (Recommended immediate solution):**

1. Install PageFind: `npm install pagefind`
2. Add to your Docusaurus build process
3. Initialize search in your theme
4. Customize UI to match your educational book design
5. Test with Urdu-English mixed content

**For future DocSearch implementation:**

1. Monitor application status on https://docsearch.algolia.com
2. Prepare your content according to DocSearch guidelines
3. Apply as soon as applications reopen
4. Migrate from PageFind to DocSearch seamlessly

## 9. Conclusion

While Algolia DocSearch remains the gold standard for documentation search, its current application pause requires consideration of alternatives. For your Urdu-English educational book website:

- **PageFind** offers the fastest path to production with good multilingual support
- **Typesense** provides a more feature-rich solution comparable to DocSearch
- **DocSearch** remains the best long-term solution once applications reopen

The mixed-language nature of your content (Urdu script with English technical terms) is well-supported by modern search solutions, and proper content structuring will ensure excellent search relevance for your users.

## 10. Resources

- [DocSearch Documentation](https://docsearch.algolia.com/docs)
- [PageFind Documentation](https://pagefind.app)
- [Typesense DocSearch Scraper](https://github.com/typesense/docsearch-scraper)
- [Docusaurus Search Configuration](https://docusaurus.io/docs/search)
- [Multilingual Search Best Practices](https://www.algolia.com/blog/implementing-multilingual-search)