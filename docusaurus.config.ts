import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

const config: Config = {
  title: "Physical AI & Humanoid Robotics",
  tagline: "A Comprehensive Guide to Embodied Intelligence",
  favicon: "img/logo.png",

  url: "https://mrowaisabdullah.github.io",
  baseUrl: "/ai-humanoid-robotics/",

  organizationName: "mrowaisabdullah",
  projectName: "ai-book",

  markdown: {
    hooks: {
      onBrokenMarkdownLinks: "warn",
    },
  },

  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.ts",
          editUrl:
            "https://github.com/mrowaisabdullah/ai-humanoid-robotics/tree/main/",
        },
        blog: false,
        theme: {
          customCss: "./src/css/custom.css",
        },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    [
      "@docusaurus/plugin-ideal-image",
      {
        quality: 70,
        max: 1030,
        min: 640,
        steps: 2,
        disableInDev: false,
      },
    ],
  ],

  themeConfig: {
    image: "img/logo.png",
    colorMode: {
      defaultMode: "dark",
      disableSwitch: false,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: "Physical AI",
      logo: {
        alt: "AI Humanoid Robotics Logo",
        src: "img/logo.png",
      },
      items: [
        {
          type: "docSidebar",
          sidebarId: "tutorialSidebar",
          position: "left",
          label: "Read Book",
        },
        {
          href: "https://github.com/mrowaisabdullah/ai-humanoid-robotics",
          label: "GitHub",
          position: "right",
          className: "header-github-link", // Class to control mobile visibility
        },
      ],
    },
    docs: {
      sidebar: {
        hideable: true,
        autoCollapseCategories: true,
      },
    },
    footer: {
      style: "light",
      links: [
        {
          title: "Course Material",
          items: [
            {
              label: "Introduction",
              to: "/docs/intro",
            },
          ],
        },
        {
          title: "Community",
          items: [
            {
              label: "Discord",
              href: "https://discord.gg/panaversity",
            },
            {
              label: "Twitter",
              href: "https://twitter.com/panaversity",
            },
          ],
        },
        {
          title: "More",
          items: [
            {
              label: "GitHub Repo",
              href: "https://github.com/mrowaisabdullah/ai-humanoid-robotics",
            },
            {
              label: "Report Issue",
              href: "https://github.com/mrowaisabdullah/ai-humanoid-robotics/issues",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Physical AI & Humanoid Robotics. Designed with Spec-Driven Development.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ["python", "bash", "json"],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
