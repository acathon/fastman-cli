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

  markdown: {
    mermaid: true,
  },

  themes: [
    '@docusaurus/theme-mermaid',
    '@docusaurus/theme-live-codeblock',
  ],

  headTags: [
    {
      tagName: 'meta',
      attributes: {
        name: 'author',
        content: 'Fastman Contributors',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        name: 'robots',
        content: 'index, follow',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        property: 'og:type',
        content: 'website',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        property: 'og:title',
        content: 'Fastman — The Elegant CLI for FastAPI Artisans',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        property: 'og:description',
        content: 'Laravel-inspired CLI tool for FastAPI. Generate projects, scaffold features, manage databases, and deploy with confidence.',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        property: 'og:url',
        content: 'https://acathon.github.io/fastman-cli/',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        property: 'og:image',
        content: 'https://acathon.github.io/fastman-cli/img/fastman-social.png',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        name: 'twitter:card',
        content: 'summary_large_image',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        name: 'twitter:title',
        content: 'Fastman — The Elegant CLI for FastAPI Artisans',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        name: 'twitter:description',
        content: 'Laravel-inspired CLI tool for FastAPI. Generate projects, scaffold features, manage databases, and deploy with confidence.',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        name: 'twitter:image',
        content: 'https://acathon.github.io/fastman-cli/img/fastman-social.png',
      },
    },
    {
      tagName: 'link',
      attributes: {
        rel: 'canonical',
        href: 'https://acathon.github.io/fastman-cli/',
      },
    },
    {
      tagName: 'link',
      attributes: {
        rel: 'preconnect',
        href: 'https://fonts.googleapis.com',
      },
    },
    {
      tagName: 'script',
      attributes: {
        type: 'application/ld+json',
      },
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'SoftwareApplication',
        name: 'Fastman',
        description: 'Laravel-inspired CLI tool for FastAPI. Generate projects, scaffold features, manage databases, and deploy with confidence.',
        applicationCategory: 'DeveloperApplication',
        operatingSystem: 'Windows, macOS, Linux',
        url: 'https://acathon.github.io/fastman-cli/',
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'USD',
        },
        softwareVersion: '0.3.6',
        programmingLanguage: 'Python',
      }),
    },
  ],

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
          showLastUpdateAuthor: true,
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
      { name: 'keywords', content: 'fastapi, cli, python, framework, scaffold, generator, fastman, authentication, keycloak, database, migrations, docker, deployment' },
      { name: 'description', content: 'Laravel-inspired CLI tool for FastAPI. Generate projects, scaffold features, manage databases, and deploy with confidence.' },
      { name: 'google-site-verification', content: 'YOUR_VERIFICATION_CODE' },
    ],

    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },

    announcementBar: {
      id: 'v0.3.6',
      content: '🎉 <strong>Fastman v0.3.6</strong> is out! Keycloak now starts safely when the IDP is unavailable, uses non-destructive SSL certificate handling, and documents admin credentials more clearly. <a href="/fastman-cli/docs/whats-new">Learn more</a>',
      backgroundColor: '#2563eb',
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
          to: '/docs/whats-new',
          position: 'left',
          label: "What's New",
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
