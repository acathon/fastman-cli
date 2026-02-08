import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Fastman',
  tagline: 'The elegant CLI for FastAPI artisans',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://acathon.github.io',
  baseUrl: '/fastman-cli/',

  organizationName: 'acathon',
  projectName: 'fastman-cli',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/acathon/fastman-cli/tree/main/docs/',
          showLastUpdateTime: true,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/fastman-social.png',

    metadata: [
      { name: 'keywords', content: 'fastapi, cli, python, framework, scaffold, generator' },
      { name: 'twitter:card', content: 'summary_large_image' },
    ],

    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },

    announcementBar: {
      id: 'v0.3.0',
      content: '🎉 <strong>Fastman v0.3.0</strong> is out! Performance improvements and Laravel-style CLI output. <a href="/docs/intro#whats-new">Learn more</a>',
      backgroundColor: '#0ea5e9',
      textColor: '#ffffff',
      isCloseable: true,
    },

    navbar: {
      title: 'Fastman',
      logo: {
        alt: 'Fastman Logo',
        src: 'img/fastman-logo.png',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Documentation',
        },
        {
          to: '/docs/commands/project',
          position: 'left',
          label: 'Commands',
        },
        {
          href: 'https://github.com/acathon/fastman-cli',
          position: 'right',
          className: 'header-github-link',
          'aria-label': 'GitHub repository',
        },
      ],
    },

    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            { label: 'Getting Started', to: '/docs/intro' },
            { label: 'Architecture', to: '/docs/concepts/architecture' },
            { label: 'Commands', to: '/docs/commands/project' },
          ],
        },
        {
          title: 'Community',
          items: [
            { label: 'GitHub', href: 'https://github.com/acathon/fastman-cli' },
            { label: 'Issues', href: 'https://github.com/acathon/fastman-cli/issues' },
            { label: 'Discussions', href: 'https://github.com/acathon/fastman-cli/discussions' },
          ],
        },
        {
          title: 'More',
          items: [
            { label: 'PyPI', href: 'https://pypi.org/project/fastman/' },
            { label: 'Changelog', href: 'https://github.com/acathon/fastman-cli/releases' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Fastman. Built with Docusaurus.`,
    },

    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'python', 'json', 'yaml', 'toml'],
    },

    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
