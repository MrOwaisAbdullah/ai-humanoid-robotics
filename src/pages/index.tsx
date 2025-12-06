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
            Building Modern Educational Content with Cutting-Edge Web Technologies
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
              <div className={styles.statNumber}>4</div>
              <div className={styles.statLabel}>Modules</div>
            </div>
            <div className={styles.stat}>
              <div className={styles.statNumber}>50+</div>
              <div className={styles.statLabel}>Lessons</div>
            </div>
            <div className={styles.stat}>
              <div className={styles.statNumber}>100%</div>
              <div className={styles.statLabel}>Practical</div>
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
        <section className={styles.features}>
          <div className="container">
            <div className="row">
              <div className="col col--12 text-center mb-12">
                <h2 className={styles.sectionTitle}>
                  What You'll Build
                </h2>
                <p className={styles.sectionSubtitle}>
                  Go from zero to a production-ready educational platform
                </p>
              </div>
            </div>
            <div className="row">
              <div className="col col--4">
                <div className={clsx('glass-card p-8 h-full hover-lift', styles.featureCard)}>
                  <div className="text-4xl mb-4 opacity-80">⚙️</div>
                  <h3>Modern Tech Stack</h3>
                  <p>
                    Docusaurus 3.9, TypeScript, React 19, and Tailwind CSS v4
                    create a powerful foundation for your content.
                  </p>
                </div>
              </div>
              <div className="col col--4">
                <div className={clsx('glass-card p-8 h-full hover-lift', styles.featureCard)}>
                  <div className="text-4xl mb-4 opacity-80">🎨</div>
                  <h3>AI-Native Design</h3>
                  <p>
                    Glassmorphism effects, dark-first design, and responsive layouts
                    that look amazing on every device.
                  </p>
                </div>
              </div>
              <div className="col col--4">
                <div className={clsx('glass-card p-8 h-full hover-lift', styles.featureCard)}>
                  <div className="text-4xl mb-4 opacity-80">🚀</div>
                  <h3>Production Ready</h3>
                  <p>
                    Automated deployments, performance optimizations, and WCAG AA
                    accessibility compliance out of the box.
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
                    Ready to Start Building?
                  </h2>
                  <p className={styles.ctaDescription}>
                    Join thousands of developers creating modern educational content
                    with cutting-edge tools and best practices.
                  </p>
                </div>
                <div className="col col--4">
                  <div className={styles.ctaButton}>
                    <Link
                      className="button button--primary button--lg w-full hover-lift"
                      to="/docs/intro">
                      Get Started Now
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
