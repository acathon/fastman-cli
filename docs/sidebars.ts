import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    'installation',
    {
      type: 'category',
      label: 'Getting Started',
      items: ['getting-started/first-project', 'getting-started/directory-structure'],
    },
    {
      type: 'category',
      label: 'Core Concepts',
      items: [
        'concepts/architecture',
        'concepts/database',
        'concepts/authentication',
      ],
    },
    {
      type: 'category',
      label: 'Command Reference',
      items: [
        'commands/scaffolding',
        'commands/database',
        'commands/utilities',
        'commands/project',
      ],
    },
    {
      type: 'category',
      label: 'Advanced',
      items: [
        'advanced/custom-commands',
        'advanced/production-build',
      ],
    },
    'deployment',
  ],
};

export default sidebars;
