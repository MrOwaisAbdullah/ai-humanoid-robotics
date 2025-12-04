import React from 'react';
import clsx from 'clsx';
import styles from './HomepageFeatures.module.css';

const FeatureList = [
  {
    title: 'Modern Development',
    icon: '⚡',
    description: 'Learn cutting-edge web development with Docusaurus 3.9, TypeScript, and the latest React features.',
  },
  {
    title: 'AI-Native Design',
    icon: '🎨',
    description: 'Master modern UI/UX patterns with glassmorphism effects, dark themes, and responsive design.',
  },
  {
    title: 'Production Ready',
    icon: '🚀',
    description: 'Deploy professional sites with automated workflows, performance optimization, and accessibility.',
  },
  {
    title: 'Educational Focus',
    icon: '📚',
    description: 'Build content that teaches effectively with interactive examples and clear explanations.',
  },
  {
    title: 'Best Practices',
    icon: '✨',
    description: 'Follow industry standards for code quality, testing, documentation, and maintenance.',
  },
  {
    title: 'Community Driven',
    icon: '🤝',
    description: 'Join a growing community of developers building modern educational content.',
  },
];

function Feature({icon, title, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4', styles.feature)}>
      <div className={clsx('glass-card p-6 h-full text-center', styles.featureCard)}>
        <div className={styles.featureIcon}>{icon}</div>
        <h3 className={styles.featureTitle}>{title}</h3>
        <p className={styles.featureDescription}>{description}</p>
      </div>
    </div>
  );
}

interface FeatureItem {
  icon: string;
  title: string;
  description: string;
}

export default function HomepageFeatures(): JSX.Element {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          <div className="col col--12 text-center mb-8">
            <h2 className={styles.sectionTitle}>
              Why This Approach?
            </h2>
            <p className={styles.sectionSubtitle}>
              Modern tools and techniques for creating exceptional educational experiences
            </p>
          </div>
        </div>
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}