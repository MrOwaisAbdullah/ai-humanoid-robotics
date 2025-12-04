import React from 'react';
import Link from '@docusaurus/Link';
import clsx from 'clsx';

export default function Module1Overview(): JSX.Element {
  return (
    <div className="module-overview">
      <h1
        className="module-title"
        style={{
          fontSize: '1.875rem',
          fontWeight: '700',
          marginBottom: '2rem',
          background: 'linear-gradient(135deg, #0d9488 0%, #14b8a6 50%, #2dd4bf 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          marginTop: 0,
          lineHeight: 1.2
        }}
      >
        Building the Foundation
      </h1>

      <p style={{ fontSize: '1.125rem', lineHeight: '1.7', marginBottom: '2rem', color: 'var(--ifm-font-color-base)' }}>
        Welcome to Module 1! This module focuses on establishing the technical foundation for your modern educational content platform. We'll set up a production-ready Docusaurus site with cutting-edge tools and minimalist design aesthetics.
      </p>

      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: 'var(--ifm-heading-color)' }}>
          🎯 Module Objectives
        </h2>
        <p style={{ marginBottom: '1rem', color: 'var(--ifm-font-color-base)' }}>
          By the end of this module, you will have:
        </p>
        <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', color: 'var(--ifm-font-color-base)' }}>
          <li>✅ A fully configured Docusaurus 3.9 project with TypeScript</li>
          <li>✅ Modern minimalist design system with Tailwind CSS v4</li>
          <li>✅ GitHub Pages deployment with automated workflows</li>
          <li>✅ Performance optimizations and accessibility features</li>
          <li>✅ A working development environment ready for content creation</li>
        </ul>
      </div>

      <div className="minimal-card p-6" style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', color: 'var(--ifm-heading-color)' }}>
          🛠️ Required Tools
        </h3>
        <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', color: 'var(--ifm-font-color-base)' }}>
          <li><strong>Node.js 20+</strong> - Download from <a href="https://nodejs.org" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--ifm-color-primary)' }}>nodejs.org</a></li>
          <li><strong>Git</strong> - Download from <a href="https://git-scm.com" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--ifm-color-primary)' }}>git-scm.com</a></li>
          <li><strong>GitHub Account</strong> - Create at <a href="https://github.com" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--ifm-color-primary)' }}>github.com</a></li>
          <li><strong>Code Editor</strong> - VS Code recommended</li>
        </ul>
      </div>

      <div className="flex flex-col gap-4 mt-8">
        <Link
          to="/docs/modules/docusaurus-installation"
          className="button button--primary button--lg"
          style={{ maxWidth: 'fit-content' }}>
          Start with Docusaurus Installation →
        </Link>

        <div className="text-center text-sm" style={{ color: 'var(--color-fg-muted)' }}>
          Or skip to any section that interests you using the sidebar navigation
        </div>
      </div>

      <div className="minimal-card p-6 mt-8" style={{
        background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.1), rgba(45, 212, 191, 0.1))'
      }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: 'var(--ifm-heading-color)' }}>
          💡 Pro Tip
        </h3>
        <p style={{ fontSize: '0.875rem', lineHeight: '1.6', color: 'var(--ifm-font-color-base)' }}>
          While going through this module, take breaks between major sections.
          Each section builds on concepts from the previous ones, so understanding
          the fundamentals is crucial for success in later modules.
        </p>
      </div>
    </div>
  );
}