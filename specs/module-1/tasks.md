# Module 1: Tasks

- [ ] **Initialize Project** <!-- id: 0 -->
    - [ ] Run `npx create-docusaurus@latest . classic --typescript --force` <!-- id: 1 -->
    - [ ] Clean up default blog/docs to match structure. <!-- id: 2 -->

- [ ] **Setup Tailwind CSS v4** <!-- id: 3 -->
    - [ ] Install dependencies: `npm install -D tailwindcss @tailwindcss/postcss postcss` <!-- id: 4 -->
    - [ ] Create `src/plugins/tailwind-config.js` (Docusaurus plugin for PostCSS). <!-- id: 5 -->
    - [ ] Register plugin in `docusaurus.config.ts`. <!-- id: 6 -->
    - [ ] Add Tailwind directives to `src/css/custom.css`. <!-- id: 7 -->

- [ ] **Implement Design System & Assets** <!-- id: 8 -->
    - [ ] Install `framer-motion` and `lucide-react`. <!-- id: 9 -->
    - [ ] Define custom CSS variables for gradients/glassmorphism in `custom.css`. <!-- id: 10 -->

- [ ] **Build Landing Page Components** <!-- id: 11 -->
    - [ ] Create `src/components/Landing/HeroSection.tsx`. <!-- id: 12 -->
    - [ ] Create `src/components/Landing/FeatureGrid.tsx`. <!-- id: 13 -->
    - [ ] Create `src/components/Landing/ModuleTimeline.tsx`. <!-- id: 14 -->
    - [ ] Update `src/pages/index.tsx` to assemble the page. <!-- id: 15 -->

- [ ] **Implement Bonus UI (Doc Buttons)** <!-- id: 16 -->
    - [ ] Swizzle DocItem/Content: `npm run swizzle @docusaurus/theme-classic DocItem/Content -- --wrap`. <!-- id: 17 -->
    - [ ] Modify wrapper to include "Personalize" and "Translate" buttons. <!-- id: 18 -->

- [ ] **Configure Deployment** <!-- id: 19 -->
    - [ ] Update `docusaurus.config.ts` with GitHub Pages settings. <!-- id: 20 -->
    - [ ] Create `.github/workflows/deploy.yml`. <!-- id: 21 -->

- [ ] **Verification** <!-- id: 22 -->
    - [ ] Run `npm run build`. <!-- id: 23 -->
    - [ ] Verify styling and animations locally. <!-- id: 24 -->
