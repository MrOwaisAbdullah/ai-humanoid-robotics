# Module 1: Book Foundation Specification

## 1. Overview
This module establishes the foundational structure for the "Physical AI & Humanoid Robotics" book using Docusaurus 3.9. The goal is to create a visually stunning, production-ready static site hosted on GitHub Pages with a modern, "AI-Native" aesthetic.

## 2. Framework & Architecture

### 2.1 Core Framework
*   **Framework**: Docusaurus 3.9 (Latest).
*   **Language**: TypeScript/JavaScript (React).
*   **Styling**: Tailwind CSS v4.
*   **Package Manager**: npm.

### 2.2 Directory Structure
```
ai-book/
├── .github/
│   └── workflows/
│       └── deploy.yml       # GitHub Actions workflow
├── docs/                    # Markdown content
│   ├── intro.md
│   └── ...
├── src/
│   ├── components/
│   │   ├── HomepageFeatures/
│   │   └── ...
│   ├── css/
│   │   └── custom.css       # Tailwind imports & custom styles
│   ├── pages/
│   │   └── index.tsx        # Modern Landing Page
│   └── theme/               # Swizzled components (if needed)
├── static/
│   └── img/
├── docusaurus.config.ts     # Main configuration
├── sidebars.ts              # Sidebar structure
├── tailwind.config.js       # Tailwind configuration
└── package.json
```

## 3. User Interface (UI) & User Experience (UX)

### 3.1 Theme
*   **Aesthetic**: "AI-Native", Professional, Modern Tech-focused.
*   **Color Palette**:
    *   **Primary**: Deep Indigo (`#4f46e5` - Indigo 600)
    *   **Primary Light**: Lighter Indigo (`#6366f1` - Indigo 500)
    *   **Primary Dark**: Deeper Indigo (`#4338ca` - Indigo 700)
    *   **Secondary**: Subtle Teal (`#14b8a6` - Teal 500)
    *   **Background Dark**: Professional Slate (`#0f172a` - Slate 900)
    *   **Background Light**: Clean White (`#ffffff`)
    *   **Text Dark**: High contrast white (`#f8fafc` - Slate 50)
    *   **Text Light**: Professional Slate (`#1e293b` - Slate 800)
    *   **Muted**: Subtle Slate (`#94a3b8` - Slate 400)
*   **Typography**:
    *   **Font Family**: Inter (wght: 300;400;500;600;700;800) - Professional sans-serif
    *   **Monospace**: JetBrains Mono (wght: 400;500;600) - Code and technical content
    *   **Rendering**: Antialiased, optimized letter spacing
*   **Effects**:
    *   **Glassmorphism**: `backdrop-filter: blur(16px)`, translucent backgrounds (`rgba(30, 41, 59, 0.7)` in dark mode)
    *   **Professional Gradients**: Indigo to Cyan (`#4f46e5` to `#06b6d4`) for text and accents
    *   **Animations**: Smooth fade-ins (`fadeInUp`, `gradientMove`, `float`), transform-based hover effects
    *   **Premium Shadows**: Layered box shadows with proper depth and blur

### 3.2 Landing Page (`src/pages/index.tsx`)
*   **Hero Section**:
    *   Full viewport height with professional gradient background
    *   Premium Indigo-to-Cyan gradient text effects
    *   Headline: "The Future of Physical AI & Humanoid Robotics" with professional gradient text
    *   Subheadline: "A comprehensive guide to embodied intelligence"
    *   CTA Button: "Start Reading" with hover-lift effect and professional styling
*   **Features Grid**:
    *   Professional glass-card components with backdrop blur effects
    *   3-4 cards highlighting key topics (ROS 2, Isaac Sim, VLA, Deep Learning)
    *   Hover effects: translateY(-2px) with premium shadows and border transitions
    *   Consistent border-radius (0.75rem) and professional spacing
*   **Course Overview**:
    *   Visual timeline of the 4 Modules with fade-in animations
    *   Professional pagination styling with hover transformations
*   **Footer**:
    *   Multi-column layout with rich dark theme (`#0b0f19`)
    *   Professional borders with subtle indigo highlights
    *   Premium shadow effects for depth perception
    *   Clean typography with Inter font and proper letter spacing

### 3.3 Chapter Layout
*   **Standard Doc Page**: Professional typography with Inter font family and antialiasing.
*   **Navigation**: Premium navbar with backdrop blur (`blur(16px)`) and gradient title text.
*   **Button System**:
    *   Robust flexbox centering with professional padding (12px 32px for large buttons)
    *   Consistent border-radius (0.5rem) and letter spacing (0.01em)
    *   Hover effects with smooth transitions and professional shadows
*   **Edit Page Link**: Styled as a pill button with hover transformations and indigo accent colors.
*   **Pagination**: Professional styling with glassmorphism effects and hover lift animations.
*   **Bonus UI Placeholders**:
    *   Add buttons "Personalize" and "Translate" with professional glass-card styling.
    *   Implementation: Wrapper component with hover-lift effects and proper spacing.
    *   Current state: Visual only (toast "Coming Soon" on click with professional styling).

## 4. Configuration & Deployment

### 4.1 Docusaurus Config (`docusaurus.config.ts`)
*   **Base URL**: `/ai-book/` (for GitHub Pages).
*   **URL**: `https://mrowaisabdullah.github.io`.
*   **Organization**: `mrowaisabdullah`.
*   **Project**: `ai-book`.
*   **Presets**: `classic` (docs, blog: false, theme).
*   **Theme Config**:
    *   **Navbar**: Professional backdrop blur with gradient title text
    *   **Footer**: Rich dark theme (`#0b0f19`) with indigo highlights
    *   **Color Mode**: Dark preferred with professional slate color scheme
    *   **Custom CSS Variables**:
      - Primary Indigo (`--ifm-color-primary: #4f46e5`)
      - Professional backgrounds (`--ifm-background-color: #0f172a`)
      - Clean typography (`--ifm-font-family-base: 'Inter'`)
      - Premium button styling with consistent border-radius and padding

### 4.2 Deployment (`.github/workflows/deploy.yml`)
*   **Trigger**: Push to `main`.
*   **Steps**:
    *   Checkout.
    *   Setup Node.js.
    *   Install dependencies.
    *   Build Docusaurus.
    *   Deploy to `gh-pages` branch.

## 5. Accessibility & Performance
*   **Lighthouse Targets**:
    *   Performance > 90.
    *   Accessibility > 90 (WCAG AA).
*   **Professional Design Practices**:
    *   **High Contrast Ratios**: Professional Indigo (#4f46e5) on Slate (#0f172a) provides excellent contrast
    *   **Typography**: Antialiased Inter font with optimized letter spacing for readability
    *   **Focus Management**: Professional focus-ring utilities with proper visual indicators
    *   **Reduced Motion**: Accessibility improvements with animation-duration control for sensitive users
    *   **Responsive Design**: Mobile-first approach with proper breakpoints and scaling
    *   **Semantic HTML**: Proper document structure with meaningful element usage
    *   **Professional Animations**: Smooth, GPU-accelerated transforms with fallbacks
*   **Dark Mode Support**: Professional slate-based dark theme optimized for extended reading sessions

## 6. Success Criteria
*   [ ] Docusaurus 3.9 initialized and running.
*   [ ] Tailwind CSS v4 configured and working.
*   [ ] Modern Landing Page implemented with requested UI effects.
*   [ ] GitHub Actions workflow created.
*   [ ] "Personalize" & "Translate" buttons visible on doc pages.
