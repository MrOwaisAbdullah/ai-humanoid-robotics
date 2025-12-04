/sp.specify
Build the foundational Frontend structure for the "Physical AI & Humanoid Robotics" book using Docusaurus 3.9.

**Context & Goals:**
This is Module 1 of a hackathon project. The goal is to set up a visually stunning, production-ready static site hosted on GitHub Pages. We need to secure base points for "Book Creation" and prepare UI elements for bonus features (personalization/translation) early.

**Requirements:**

1.  **Framework**: Docusaurus 3.9 (Latest).
    *   *Action*: Use `mcp__context7__get-library-docs` with libraryID="docusaurus" to check for the latest configuration best practices (docusaurus.config.js).
2.  **Theme & UI**:
    *   Modern, "AI-Native" aesthetic.
    *   Use Tailwind CSS v4 (configure via PostCSS).
    *   Gradient backgrounds, glassmorphism effects for cards/sidebars.
    *   Typography: Inter or Roboto for body, clean headers.
    *   **Dark Mode**: First-class support (default to dark mode if possible/appropriate for AI theme).
3.  **Layout Customization**:
    *   Standard Doc layout for chapters.
    *   **Bonus Prep (UI Only)**: Add "Personalize" and "Translate to Urdu" buttons to the top of the Chapter layout (Swizzle the DocItem component if necessary, or use a wrapper). These buttons can be non-functional for now (toast notification "Coming soon").
4.  **Deployment (GitHub Pages)**:
    *   Configure `docusaurus.config.js` for GitHub Pages (`baseUrl`, `url`, `organizationName`, `projectName`).
    *   Create a GitHub Actions workflow (`.github/workflows/deploy.yml`) for automated deployment on push to `main`.
5.  **Pages**:
    *   `index.js` (Landing Page): 
        *   **Hero Section**: High-impact, immersive design. Deep dark background with animated gradient mesh or subtle particle effects. Large, bold typography with gradient text for the title. Primary CTA ("Start Reading") with a "glow" effect.
        *   **Features Grid**: Use **Glassmorphism** (frosted glass) for cards: `backdrop-blur-md`, `bg-white/5`, `border-white/10`. subtle hover effects (scale up, glow, shadow-lg).
        *   **Course Overview**: A visual timeline or step-by-step path showing the 4 Modules.
        *   **Animations**: Implement smooth scroll animations (fade-in, slide-up) for all sections using `framer-motion` or CSS keyframes. Ensure "smooth" feel, not jerky.
        *   **Spacing & Contrast**: Generous padding (section padding `py-20` or `py-24`). strict WCAG AA contrast ratios.
        *   **Footer**: Modern, multi-column layout with social links and copyright.

**Technical Constraints:**
- Must use Tailwind CSS for styling.
- Must be responsive (mobile-first).
- Must pass Lighthouse accessibility checks (Contrast, ARIA).

**Deliverable:**
- A fully configured Docusaurus repository.
- A running landing page.
- Deployment workflow committed.





