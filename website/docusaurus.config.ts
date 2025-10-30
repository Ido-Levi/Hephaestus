import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'Hephaestus',
  tagline: 'Semi-Structured Agentic Framework with Trajectory Analysis',
  favicon: 'img/anvil_icon.png',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: 'https://ido-levi.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/Hephaestus/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'Ido-Levi', // Usually your GitHub org/user name.
  projectName: 'Hephaestus', // Usually your repo name.

  onBrokenLinks: 'warn', // Changed from 'throw' to allow build with broken links

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  // Enable Mermaid diagrams
  markdown: {
    mermaid: true,
  },
  themes: [
    '@docusaurus/theme-mermaid',
    [
      require.resolve("@easyops-cn/docusaurus-search-local"),
      {
        hashed: true,
        language: ["en"],
        highlightSearchTermsOnTargetPage: true,
        explicitSearchResultPath: true,
        docsRouteBasePath: '/docs',
        indexBlog: false,
        indexPages: false,
        searchResultLimits: 8,
        searchResultContextMaxLength: 50,
        useAllContextsWithNoSearchContext: false,
        searchBarShortcutHint: true,
        searchBarPosition: "right",
      },
    ],
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/Ido-Levi/Hephaestus/tree/main/website/',
        },
        blog: false, // Disable blog for now
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Replace with your project's social card
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Hephaestus',
      logo: {
        alt: 'Hephaestus Logo',
        src: 'img/anvil_icon.png',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Documentation',
        },
        {
          to: 'docs/getting-started/quick-start',
          position: 'left',
          label: 'Quick Start',
        },
        {
          href: 'https://github.com/Ido-Levi/Hephaestus',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Getting Started',
              to: 'docs/',
            },
            {
              label: 'Core Systems',
              to: 'docs/core/monitoring-implementation',
            },
            {
              label: 'SDK Guide',
              to: 'docs/sdk/README',
            },
          ],
        },
        {
          title: 'Resources',
          items: [
            {
              label: 'Quick Start',
              to: 'docs/getting-started/quick-start',
            },
            {
              label: 'Best Practices',
              to: 'docs/guides/best-practices',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/Ido-Levi/Hephaestus',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'Workflow Guides',
              to: 'docs/guides/phases-system',
            },
            {
              label: 'Ticket Tracking',
              to: 'docs/guides/ticket-tracking',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Hephaestus. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
