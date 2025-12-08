import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Lab Infrastructure',
      items: [
        {
          type: 'category',
          label: 'Workstation Setup',
          items: [
            'lab-infrastructure/workstation-setup/index',
            'lab-infrastructure/workstation-setup/gpu-optimization',
          ],
        },
        {
          type: 'category',
          label: 'Edge AI Hardware',
          items: [
            'lab-infrastructure/jetson-setup/index',
            'lab-infrastructure/realsense-setup/index',
          ],
        },
        'lab-infrastructure/budget-calculator',
        'lab-infrastructure/cloud-alternatives/index',
      ],
    },
    {
      type: 'category',
      label: 'Course Content',
      collapsed: false,
      items: [
        {
          type: 'category',
          label: 'Module 1: Foundations',
          collapsed: false,
          items: [
            'part-1-foundations/chapter-1-introduction',
            'part-1-foundations/chapter-2-sensors-perception',
            'part-1-foundations/chapter-3-state-estimation',
            'part-1-foundations/chapter-4-motion-planning',
            'part-1-foundations/chapter-5-integration',
          ],
        },
        {
          type: 'category',
          label: 'Module 2: Nervous System',
          collapsed: false,
          items: [
            'part-2-nervous-system/chapter-6-ros2-architecture',
            'part-2-nervous-system/chapter-7-ros2-nodes-python',
            'part-2-nervous-system/chapter-8-launch-systems',
          ],
        },
        {
          type: 'category',
          label: 'Module 3: Motion and Control',
          collapsed: false,
          items: [
            'part-3-motion-control/chapter-9-kinematics-dynamics',
            'part-3-motion-control/chapter-10-balance-locomotion',
            'part-3-motion-control/chapter-11-manipulation-grasping',
          ],
        },
        {
          type: 'category',
          label: 'Module 4: Applications and Advanced Topics',
          collapsed: false,
          items: [
            'part-4-applications/chapter-12-computer-vision',
            'part-4-applications/chapter-13-machine-learning',
            'part-4-applications/chapter-14-human-robot-interaction',
            'part-4-applications/chapter-15-future-physical-ai',
          ],
        },
      ],
    },
  ],
};

export default sidebars;