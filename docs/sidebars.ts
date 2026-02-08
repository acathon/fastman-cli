import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    'whats-new',
    'installation',
    {
      type: 'category',
      label: 'Getting Started',
      collapsed: false,
      items: ['getting-started/first-project', 'getting-started/directory-structure'],
    },
    {
      type: 'category',
      label: 'Core Concepts',
      items: [
        'concepts/architecture',
        'concepts/examples',
        'concepts/database',
        'concepts/authentication',
      ],
    },
    {
      type: 'category',
      label: 'Commands',
      items: [
        'commands/project',
        'commands/scaffolding',
        'commands/database',
        'commands/utilities',
      ],
    },
    {
      type: 'category',
      label: 'Advanced',
      items: [
        'advanced/tinker',
        'advanced/custom-commands',
        'advanced/production-build',
      ],
    },
    'deployment',
  ],
};

export default sidebars;
