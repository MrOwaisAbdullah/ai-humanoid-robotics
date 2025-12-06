# Data Model: Docusaurus Setup & Configuration

**Date**: 2025-12-04
**Feature**: 001-docusaurus-setup

## Site Configuration Data Model

### Core Site Metadata

```typescript
interface SiteConfig {
  title: string; // "Physical AI & Humanoid Robotics - Comprehensive Guide"
  tagline: string; // "Production-ready educational content"
  url: string; // "https://[username].github.io"
  baseUrl: string; // "/ai-humanoid-robotics/"
  favicon?: string; // Path to favicon file
  trailingSlash?: boolean; // URL trailing slash behavior
}
```

### GitHub Pages Configuration

```typescript
interface GitHubPagesConfig {
  organizationName: string; // GitHub username/organization
  projectName: string; // Repository name ("ai-book")
  deploymentBranch?: string; // "gh-pages" (default)
  githubHost?: string; // "github.com" (default)
  githubPort?: string; // "22" (default)
}
```

### Theme Configuration

```typescript
interface ThemeConfig {
  colorMode: {
    defaultMode: "dark" | "light"; // "dark" (per spec)
    disableSwitch: boolean; // false (allow manual toggle)
    respectPrefersColorScheme: boolean;
  };
  navbar: {
    title: string; // Book title
    logo?: {
      alt: string; // Logo alt text
      src: string; // Logo path
      width?: number; // Logo width
      height?: number; // Logo height
    };
    items: NavbarItem[]; // Navigation items
  };
  footer: {
    style: "light" | "dark"; // "dark" for AI theme
    links: FooterLink[]; // Footer link sections
    copyright: string; // Copyright text
    logo?: {
      alt: string;
      src: string;
      href: string;
      width?: number;
      height?: number;
    };
  };
  docs: {
    sidebar: {
      hideable: boolean; // Allow sidebar hiding
      autoCollapseCategories: boolean;
    };
  };
}
```

### Design System Tokens

```typescript
interface DesignTokens {
  colors: {
    primary: {
      light: string; // "#7033ff"
      dark: string; // "#8c5cff"
    };
    background: {
      light: string; // "#fdfdfd"
      dark: string; // "#1a1b1e"
    };
    foreground: {
      light: string; // "#000000"
      dark: string; // "#f0f0f0"
    };
    semantic: {
      card: string;
      muted: string;
      accent: string;
      destructive: string;
    };
  };
  typography: {
    sansSerif: string; // "Plus Jakarta Sans"
    serif: string; // "Lora"
    mono: string; // "IBM Plex Mono"
  };
  spacing: {
    base: string; // "0.27rem"
    scale: number[]; // Spacing scale values
  };
  borderRadius: string; // "1.4rem"
  shadows: ShadowLevel[]; // 9 shadow levels (2xs to 2xl)
}
```

### Plugin Configuration

```typescript
interface PluginConfig {
  preset: {
    name: "@docusaurus/preset-classic";
    options: {
      docs: {
        path: string; // "docs"
        sidebarPath: string; // Path to sidebar config
        editUrl?: string; // GitHub edit URL
      };
      blog: boolean; // false (not using blog)
      theme: {
        customCss: string[]; // Custom CSS files
      };
    };
  };
  custom: CustomPlugin[]; // Tailwind, performance plugins
}
```

### Performance Configuration

```typescript
interface PerformanceConfig {
  future: {
    v4: {
      removeLegacyPostBuildHeadAttribute: boolean;
      useCssCascadeLayers: boolean;
    };
    experimental_faster: {
      swcJsLoader: boolean; // true for faster JS transpilation
      swcJsMinimizer: boolean; // true for faster minification
      swcHtmlMinimizer: boolean; // true for faster HTML minification
      lightningCssMinimizer: boolean; // true for faster CSS minification
      rspackBundler: boolean; // true for faster bundling
      rspackPersistentCache: boolean; // true for rebuild caching
      ssgWorkerThreads: boolean; // true for parallel SSG
      mdxCrossCompilerCache: boolean; // true for MDX caching
    };
  };
}
```

## Content Structure Model

### Chapter Metadata

```typescript
interface ChapterMetadata {
  title: string; // Chapter title
  description?: string; // Chapter description
  authors?: string[]; // Chapter authors
  tags?: string[]; // Content tags
  lastUpdated?: string; // ISO date string
  readingTime?: number; // Estimated reading time in minutes
  difficulty?: "beginner" | "intermediate" | "advanced";
  prerequisites?: string[]; // Required knowledge
}
```

### Sidebar Structure

```typescript
interface SidebarItem {
  type: "category" | "doc" | "link";
  label: string; // Display label
  customProps?: Record<string, any>;
  items?: SidebarItem[]; // Nested items for categories
  href?: string; // Link URL for type 'link'
}
```

## SEO Configuration

```typescript
interface SEOConfig {
  openGraph: {
    type: string; // "website" or "book"
    locale: string; // "en_US"
    siteName: string; // Site name
  };
  twitter: {
    handle: string; // Twitter handle
    site: string; // Twitter site
    cardType: "summary" | "summary_large_image";
  };
  structuredData: {
    book: {
      name: string; // Book title
      author: string; // Author name
      genre: string[]; // Book genres
      description: string; // Book description
    };
  };
}
```

## Validation Rules

### Site Configuration Validation

- `title` must be non-empty string
- `url` must be valid HTTPS URL
- `baseUrl` must start with "/" and end with "/"
- `organizationName` and `projectName` required for GitHub Pages

### Design Token Validation

- All color values must be valid hex codes
- Typography fonts must be web-safe or properly loaded
- Border radius must be valid CSS value
- Shadow values must follow defined pattern

### Content Validation

- Chapter titles must be unique within sidebar
- All sidebar items must have valid labels
- Custom props must be serializable

## State Transitions

### Build Process States

1. **Configuration Loading** → Validate config files
2. **Content Processing** → Parse Markdown and frontmatter
3. **Asset Optimization** → Compress images and optimize code
4. **Static Generation** → Generate HTML pages
5. **Deployment** → Push to GitHub Pages

### Theme Switching States

1. **Initial Load** → Detect system preference or use default (dark)
2. **Manual Toggle** → Switch between light/dark themes
3. **Persistence** → Store preference in localStorage

## Error Handling

### Configuration Errors

- Invalid URL formats → Default to safe values
- Missing required fields → Clear error messages with fix suggestions
- Invalid color codes → Fallback to default color palette

### Build Errors

- Markdown parsing errors → Continue with other files, report errors
- Asset optimization failures → Skip optimization, warn user
- Deployment failures → Clear error messages with troubleshooting steps

## Relationships

### Site → Theme Configuration

Site config determines theme defaults
Theme config can override site-level settings

### Content → Navigation Structure

Chapter metadata drives sidebar organization
Sidebar structure defines site navigation

### Design System → Component Styling

Design tokens provide consistent styling
Components consume design system values

### Performance → User Experience

Build optimizations affect load times
Caching strategies impact perceived performance
