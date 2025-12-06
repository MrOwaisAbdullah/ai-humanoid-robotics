# Quickstart Guide: Docusaurus Setup & Configuration

**Date**: 2025-12-04
**Feature**: 001-docusaurus-setup
**Estimated Setup Time**: 30-45 minutes

## Prerequisites

### System Requirements

- Node.js 18+ (for Docusaurus 3.9)
- npm or yarn package manager
- Git for version control
- GitHub account (for Pages deployment)

### Required Knowledge

- Basic command line familiarity
- Understanding of Markdown for content authoring
- Basic knowledge of CSS (for customizations)

## Initial Setup

### 1. Initialize Docusaurus Project

```bash
# Create new Docusaurus site with TypeScript
npx create-docusaurus@latest ai-book classic --typescript

# Navigate to project directory
cd ai-book

# Install performance optimizations
npm install --save-dev @docusaurus/faster

# Install Tailwind CSS v4
npm install --save-dev tailwindcss postcss @tailwindcss/postcss
```

### 2. Configure Basic Site Information

Edit `docusaurus.config.ts`:

```typescript
export default {
  title: "Physical AI & Humanoid Robotics - Comprehensive Guide",
  tagline: "Production-ready educational content",
  url: "https://[username].github.io",
  baseUrl: "/ai-humanoid-robotics/",

  // GitHub Pages configuration
  organizationName: "[username]",
  projectName: "ai-book",
  deploymentBranch: "gh-pages",

  // Default theme configuration
  themeConfig: {
    colorMode: {
      defaultMode: "dark", // As per specification
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    // ... rest of theme config
  },
};
```

### 3. Configure Tailwind CSS v4

Create `postcss.config.js`:

```javascript
module.exports = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

Create `tailwind.config.js`:

```javascript
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./docs/**/*.{md,mdx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          light: "#7033ff",
          dark: "#8c5cff",
        },
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "sans-serif"],
        serif: ["Lora", "serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      borderRadius: {
        DEFAULT: "1.4rem",
      },
    },
  },
};
```

## Content Structure

### 1. Create Basic Documentation Structure

```
docs/
├── intro.md                 # Introduction and getting started
├── modules/                 # Module-based organization
│   ├── module-1-overview.md # Current module content
│   ├── module-2-planning.md # Future module placeholder
│   ├── module-3-content.md  # Future module placeholder
│   └── module-4-publish.md  # Future module placeholder
└── resources/               # Additional resources
    ├── glossary.md
    └── references.md
```

### 2. Configure Sidebar

Create `docs/sidebar.js`:

```javascript
module.exports = {
  tutorialSidebar: [
    {
      type: "category",
      label: "Getting Started",
      items: ["intro"],
    },
    {
      type: "category",
      label: "Book Development Modules",
      items: [
        {
          type: "category",
          label: "Module 1: Docusaurus Setup",
          items: ["modules/module-1-overview"],
        },
        {
          type: "category",
          label: "Module 2: Content Planning",
          items: ["modules/module-2-planning"],
        },
        {
          type: "category",
          label: "Module 3: Content Creation",
          items: ["modules/module-3-content"],
        },
        {
          type: "category",
          label: "Module 4: Publishing",
          items: ["modules/module-4-publish"],
        },
      ],
    },
  ],
};
```

## Customization

### 1. Apply Design System

Create `src/css/custom.css`:

```css
:root {
  /* Light theme colors */
  --background: #fdfdfd;
  --foreground: #000000;
  --primary: #7033ff;
  --primary-foreground: #ffffff;

  /* Typography */
  --font-sans: Plus Jakarta Sans, sans-serif;
  --font-serif: Lora, serif;
  --font-mono: IBM Plex Mono, monospace;

  /* Spacing and design tokens */
  --radius: 1.4rem;
  --spacing: 0.27rem;
}

.dark {
  /* Dark theme colors */
  --background: #1a1b1e;
  --foreground: #f0f0f0;
  --primary: #8c5cff;
}

body {
  font-family: var(--font-sans);
  letter-spacing: var(--tracking-normal);
}

/* Custom theme styling */
[data-theme="dark"] {
  /* Dark mode specific styles */
}
```

### 2. Add Custom Landing Page

Replace `src/pages/index.tsx`:

```tsx
import React from "react";
import Layout from "@theme/Layout";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";

export default function Home() {
  const { siteConfig } = useDocusaurusContext();

  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <main className="container margin-vert--lg">
        <div className="hero">
          <h1 className="hero__title">{siteConfig.title}</h1>
          <p className="hero__subtitle">{siteConfig.tagline}</p>
          <div className="hero__buttons">
            <a className="button button--primary button--lg" href="/docs/intro">
              Start Reading
            </a>
          </div>
        </div>

        <div className="margin-vert--lg">
          <h2>Course Overview</h2>
          <p>
            Learn Physical AI & Humanoid Robotics through our comprehensive
            guide...
          </p>
        </div>
      </main>
    </Layout>
  );
}
```

## GitHub Pages Deployment

### 1. Configure GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "18"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Build website
        run: npm run build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./build
```

### 2. Enable GitHub Pages

1. Go to repository Settings > Pages
2. Select "GitHub Actions" as source
3. Save settings

### 3. Test Deployment

```bash
# Build locally first
npm run build

# Test the build output
npm run serve

# Commit and push to trigger deployment
git add .
git commit -m "Initial Docusaurus setup"
git push origin main
```

## Development Workflow

### 1. Local Development

```bash
# Start development server
npm start

# Open http://localhost:3000
# Site will auto-reload on changes
```

### 2. Building for Production

```bash
# Build production bundle
npm run build

# Preview production build
npm run serve
```

### 3. Content Authoring

```bash
# Create new chapter
echo "# Chapter Title\n\nChapter content..." > docs/new-chapter.md

# Add to sidebar configuration
# Edit docs/sidebar.js to include new chapter

# Test locally
npm start

# Deploy when ready
git add docs/new-chapter.md docs/sidebar.js
git commit -m "Add new chapter"
git push origin main
```

## Troubleshooting

### Common Issues

1. **Build fails with baseUrl errors**

   - Verify baseUrl in config matches repository name
   - Ensure baseUrl starts and ends with "/"

2. **Styles not loading**

   - Check Tailwind configuration
   - Verify PostCSS setup
   - Clear browser cache

3. **GitHub Pages deployment fails**
   - Check GitHub Actions logs
   - Verify repository settings allow Pages
   - Ensure build completes successfully

### Performance Optimization

```bash
# Enable faster builds (experimental)
npm run build -- --experimental-faster

# Analyze bundle size
npm run build -- --analyze

# Test performance locally
npm run build
npm run serve
```

## Next Steps

1. **Content Creation**: Start writing book content in Markdown files
2. **Customization**: Implement custom components and styling
3. **SEO Optimization**: Configure metadata and structured data
4. **Analytics**: Add Google Analytics or other tracking
5. **Testing**: Implement accessibility and performance testing

## Resources

- [Docusaurus Documentation](https://docusaurus.io/docs)
- [Tailwind CSS v4 Guide](https://tailwindcss.com/docs)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Markdown Guide](https://www.markdownguide.org/)
