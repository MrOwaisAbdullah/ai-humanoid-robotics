/**
 * Sidebar configuration for Physical AI & Humanoid Robotics book
 * Defines the navigation structure for the 4 book development modules
 */

module.exports = {
  // Main sidebar for the book content
  bookSidebar: [
    {
      type: 'doc',
      id: 'intro',
      label: 'Introduction',
    },
    {
      type: 'category',
      label: 'Module 1: Docusaurus Setup',
      collapsible: true,
      collapsed: false,
      items: [
        {
          type: 'doc',
          id: 'modules/module-1-overview',
          label: 'Module Overview',
        },
      ],
    },
    {
      type: 'category',
      label: 'Module 2: Content Planning',
      collapsible: true,
      collapsed: true,
      items: [
        {
          type: 'doc',
          id: 'modules/module-2-planning',
          label: 'Module Overview',
        },
      ],
    },
    {
      type: 'category',
      label: 'Module 3: Content Development',
      collapsible: true,
      collapsed: true,
      items: [
        {
          type: 'doc',
          id: 'modules/module-3-content',
          label: 'Module Overview',
        },
      ],
    },
    {
      type: 'category',
      label: 'Module 4: Publishing & Maintenance',
      collapsible: true,
      collapsed: true,
      items: [
        {
          type: 'doc',
          id: 'modules/module-4-publish',
          label: 'Module Overview',
        },
      ],
    },
  ],

  // Tutorial sidebar (for Docusaurus classic compatibility)
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Tutorial - Basics',
      items: [
        'tutorial-basics/create-a-document',
        'tutorial-basics/create-a-page',
        'tutorial-basics/create-a-blog-post',
        'tutorial-basics/markdown-features',
        'tutorial-basics/deploy-your-site',
        'tutorial-basics/congratulations',
      ],
    },
    {
      type: 'category',
      label: 'Tutorial - Extras',
      items: [
        'tutorial-extras/manage-docs-versions',
        'tutorial-extras/translate-your-site',
      ],
    },
  ],
};