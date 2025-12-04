# Module 1: Implementation Plan

## 1. Architecture & Tech Stack
*   **Framework**: Docusaurus 3.9 (Classic preset).
*   **Styling**: Tailwind CSS v4 (via PostCSS plugin).
*   **Animations**: Framer Motion (for React components) + CSS Keyframes.
*   **Icons**: Lucide React (modern, clean).

## 2. Styling Strategy
*   **Theme Integration**: Docusaurus classic theme + Tailwind utility classes.
*   **Dark Mode**: We will prioritize Dark Mode. Tailwind `dark:` variant will be used.
*   **Glassmorphism Utility**:
    *   Create a custom utility class `.glass-panel` in `custom.css` or use Tailwind arbitrary values: `bg-white/5 backdrop-blur-md border border-white/10`.
*   **Typography**:
    *   Headings: `font-bold tracking-tight`.
    *   Body: `text-gray-300` (in dark mode).

## 3. Component Architecture

### 3.1 Landing Page (`src/pages/index.tsx`)
Decompose into:
*   `HeroSection`: Full-screen, animated background, main CTA.
*   `FeatureGrid`: Grid of `GlassCard` components.
*   `ModuleTimeline`: Vertical or horizontal step visualization.
*   `Footer`: Standard Docusaurus footer configured in `docusaurus.config.ts`.

### 3.2 Doc Integration
*   **Goal**: Add buttons to doc pages.
*   **Method**: Swizzle `DocItem/Layout` or use `Root` theme component.
*   **Decision**: Use `Root` component to inject a wrapper, or simpler: Swizzle `DocItem/Content` to inject buttons above the content. **Selected**: Swizzle `DocItem/Content` (safest for content injection).

## 4. Deployment Strategy
*   **GitHub Actions**: Standard `deploy.yml` provided by Docusaurus docs.
*   **Config**: Ensure `baseUrl` matches repository name (`/ai-book/`).

## 5. Step-by-Step Implementation
1.  **Init**: Scaffold Docusaurus.
2.  **Tailwind**: Install & Config (PostCSS).
3.  **Theme**: Update `custom.css` with imports and base styles.
4.  **UI Components**: Build Hero, GlassCard.
5.  **Pages**: Assemble `index.tsx`.
6.  **Doc UI**: Swizzle & Add Buttons.
7.  **CI/CD**: Add workflow.
