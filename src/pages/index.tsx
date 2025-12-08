import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <div className={styles.heroContent}>
          <h1 className={clsx('professional-gradient-text', styles.heroTitle)}>
            {siteConfig.title}
          </h1>
          <p className={styles.heroSubtitle}>
            A Comprehensive Guide to Embodied Intelligence, Sim-to-Real Transfer, and Humanoid Engineering
          </p>
          <div className={styles.heroActions}>
            <Link
              className="button button--primary button--lg hover-lift"
              to="/docs/intro">
              Start Reading
            </Link>
            <Link
              className="button button--secondary button--lg hover-lift"
              to="https://github.com/mrowaisabdullah/ai-humanoid-robotics">
              View on GitHub
            </Link>
          </div>
          <div className={styles.heroStats}>
            <div className={styles.stat}>
              <div className={styles.statNumber}>15+</div>
              <div className={styles.statLabel}>Chapters</div>
            </div>
            <div className={styles.stat}>
              <div className={styles.statNumber}>ROS 2</div>
              <div className={styles.statLabel}>Humble</div>
            </div>
            <div className={styles.stat}>
              <div className={styles.statNumber}>ISAAC</div>
              <div className={styles.statLabel}>Sim Ready</div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

export default function Home(): JSX.Element {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - Modern Educational Content`}
      description="Learn to build production-ready documentation sites with Docusaurus, TypeScript, and AI-native design">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        
        <section className={styles.features}>
          <div className="container">
            <div className="row">
              <div className="col col--12 text-center mb-12">
                <h2 className={styles.sectionTitle}>
                  Who Is This For?
                </h2>
                <p className={styles.sectionSubtitle}>
                  Designed for ambitious builders ready to shape the future of robotics
                </p>
              </div>
            </div>
            <div className="row">
              <div className="col col--4">
                <div className={clsx('glass-card p-8 h-full hover-lift', styles.featureCard)}>
                  <div className="text-4xl mb-4 opacity-80">👨‍💻</div>
                  <h3>Software Engineers</h3>
                  <p>
                    Expand your skills from pure code to physical systems. Learn how to apply
                    modern AI, computer vision, and control theory to real-world hardware.
                  </p>
                </div>
              </div>
              <div className="col col--4">
                <div className={clsx('glass-card p-8 h-full hover-lift', styles.featureCard)}>
                  <div className="text-4xl mb-4 opacity-80">🎓</div>
                  <h3>Students & Researchers</h3>
                  <p>
                    Get a practical, hands-on guide to the latest in Humanoid Robotics,
                    bridging the gap between academic theory and industrial application.
                  </p>
                </div>
              </div>
              <div className="col col--4">
                <div className={clsx('glass-card p-8 h-full hover-lift', styles.featureCard)}>
                  <div className="text-4xl mb-4 opacity-80">🔧</div>
                  <h3>Robotics Hobbyists</h3>
                  <p>
                    Take your projects to the next level with professional-grade tools like
                    ROS 2, Isaac Sim, and Jetson Orin, without the steep learning curve.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.cta}>
          <div className="container">
            <div className={clsx('glass-card p-8', styles.ctaCard)}>
              <div className="row items-center">
                <div className="col col--8">
                  <h2 className={styles.ctaTitle}>
                    Ready to Build the Future?
                  </h2>
                  <p className={styles.ctaDescription}>
                    The era of Physical AI is here. Start your journey into embodied intelligence
                    and build your own humanoid robot companion today.
                  </p>
                </div>
                <div className="col col--4">
                  <div className={styles.ctaButton}>
                    <Link
                      className="button button--primary button--lg w-full hover-lift"
                      to="/docs/intro">
                      Start Learning Now
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
