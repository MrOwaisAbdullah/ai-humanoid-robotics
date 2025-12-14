import React from 'react';
import clsx from 'clsx';
import styles from './HomepageFeatures.module.css';

const FeatureList = [
  {
    title: 'Embodied Intelligence',
    icon: '🧠',
    description: 'Bridge the gap between digital AI and the physical world. Give LLMs a body and sensory perception.',
  },
  {
    title: 'ROS 2 & Isaac Sim',
    icon: '🤖',
    description: 'Master the industry-standard Robot Operating System and NVIDIA\'s photorealistic simulation environment.',
  },
  {
    title: 'Hands-On Hardware',
    icon: '🛠️',
    description: 'Build real systems with Jetson Orin, Realsense cameras, and dynamixel actuators.',
  },
  {
    title: 'Computer Vision',
    icon: '👁️',
    description: 'Implement state-of-the-art perception pipelines for depth estimation, object detection, and SLAM.',
  },
  {
    title: 'Sim-to-Real Transfer',
    icon: '🔄',
    description: 'Train policies in simulation and successfully deploy them to physical humanoid hardware.',
  },
  {
    title: 'Cognitive Architecture',
    icon: '🧩',
    description: 'Design complex nervous systems that integrate planning, memory, and multi-modal interaction.',
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
              What You Will Master
            </h2>
            <p className={styles.sectionSubtitle}>
              A comprehensive curriculum designed for the next generation of robotics engineers
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