import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: '🚀 Getting Started',
      collapsed: false,
      items: [
        'getting-started/quick-start',
        'getting-started/bootstrap-new-project',
      ],
    },
    {
      type: 'category',
      label: '🔧 Troubleshooting',
      collapsed: false,
      items: [
        'troubleshooting/agent-issues',
      ],
    },
    {
      type: 'category',
      label: '📖 Workflow Design Guides',
      collapsed: false,
      items: [
        'guides/phases-system',
        'guides/best-practices',
        'guides/guardian-monitoring',
        'guides/ticket-tracking',
        'guides/running-swebench-benchmark',
      ],
    },
    {
      type: 'category',
      label: '⚙️ Core Systems',
      items: [
        'core/agent-communication',
        'core/memory-system',
        'core/monitoring-implementation',
        'core/queue-and-task-management',
        'core/validation-system',
        'core/worktree-isolation',
        'features/diagnostic-agents',
        'features/task-deduplication',
        'features/task-results',
        'features/workflow-results',
      ],
    },
    {
      type: 'category',
      label: '🐍 Python SDK',
      items: [
        'sdk/overview',
        'sdk/phases',
        'sdk/examples',
      ],
    },
  ],
};

export default sidebars;
