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
          label: 'MODULE 1: FOUNDATIONS',
          collapsed: false,
          items: [
            'module-1-foundation/chapter-1-introduction',
            'module-1-foundation/chapter-2-sensors-perception',
            'module-1-foundation/chapter-3-state-estimation',
            'module-1-foundation/chapter-4-motion-planning',
            'module-1-foundation/chapter-5-integration',
          ],
        },
        {
          type: 'category',
          label: 'MODULE 2: NERVOUS SYSTEM',
          collapsed: true,
          items: [
            'module-2-nervous-system/chapter-6-ros2-architecture',
            'module-2-nervous-system/chapter-7-ros2-nodes-python',
            'module-2-nervous-system/chapter-8-launch-systems',
          ],
        },
        {
          type: 'category',
          label: 'MODULE 3: MOTION AND CONTROL',
          collapsed: true,
          items: [
            'module-3-motion-control/chapter-9-kinematics-dynamics',
            'module-3-motion-control/chapter-10-balance-locomotion',
            'module-3-motion-control/chapter-11-manipulation-grasping',
          ],
        },
        {
          type: 'category',
          label: 'MODULE 4: APPLICATIONS AND ADVANCED TOPICS',
          collapsed: true,
          items: [
            'module-4-applications/chapter-12-computer-vision',
            'module-4-applications/chapter-13-machine-learning',
            'module-4-applications/chapter-14-human-robot-interaction',
            'module-4-applications/chapter-15-future-physical-ai',
          ],
        },
        {
          type: 'category',
          label: 'MODULE 5: ADVANCED HUMANOIDS',
          collapsed: true,
          items: [
            'module-5-advanced-humanoids/chapter-16-bipedal-mechanics',
            'module-5-advanced-humanoids/chapter-17-advanced-locomotion',
            'module-5-advanced-humanoids/chapter-18-whole-body-control',
            'module-5-advanced-humanoids/chapter-19-case-studies',
          ],
        },
      ],
    },
  ],
};

export default sidebars;