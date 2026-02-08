import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          Fastman
        </Heading>
        <p className="hero__subtitle">
          The elegant CLI for FastAPI artisans
        </p>
        <p style={{ opacity: 0.8, marginBottom: '2rem', maxWidth: '600px', margin: '0 auto 2rem' }}>
          Generate projects, scaffold features, manage databases, and deploy with confidence.
          Laravel-inspired developer experience for FastAPI.
        </p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro">
            Get Started
          </Link>
          <Link
            className="button button--outline button--lg"
            style={{ marginLeft: '1rem', color: 'white', borderColor: 'rgba(255,255,255,0.5)' }}
            href="https://github.com/acathon/fastman-cli">
            View on GitHub
          </Link>
        </div>
      </div>
    </header>
  );
}

type FeatureItem = {
  icon: string;
  title: string;
  description: string;
};

const features: FeatureItem[] = [
  {
    icon: '🏗️',
    title: 'Project Scaffolding',
    description: 'Create production-ready FastAPI projects with one command. Choose your architecture and database.',
  },
  {
    icon: '📐',
    title: 'Multiple Architectures',
    description: 'Feature-based (vertical slices), API-versioned, or traditional layered patterns. You choose.',
  },
  {
    icon: '🗄️',
    title: 'Database Ready',
    description: 'SQLite, PostgreSQL, MySQL, Oracle, Firebase. Migrations and seeders included.',
  },
  {
    icon: '🔐',
    title: 'Auth Scaffolding',
    description: 'JWT, OAuth, or Keycloak authentication. One command setup with best practices.',
  },
  {
    icon: '📦',
    title: 'Smart Detection',
    description: 'Auto-detects uv, poetry, pipenv, or pip. Works with your preferred package manager.',
  },
  {
    icon: '🚀',
    title: 'Production Ready',
    description: 'Docker builds, config caching, code optimization. From development to deployment.',
  },
];

function Feature({ icon, title, description }: FeatureItem) {
  return (
    <div className="col col--4">
      <div className="feature-card" style={{ height: '100%', padding: '1.5rem' }}>
        <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>{icon}</div>
        <Heading as="h3" style={{ fontSize: '1.125rem', marginBottom: '0.5rem' }}>
          {title}
        </Heading>
        <p style={{ color: 'var(--ifm-color-emphasis-700)', fontSize: '0.9375rem', lineHeight: 1.6, margin: 0 }}>
          {description}
        </p>
      </div>
    </div>
  );
}

function HomepageFeatures() {
  return (
    <section style={{ padding: '4rem 0' }}>
      <div className="container">
        <div className="row" style={{ gap: '1.5rem 0' }}>
          {features.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}

function QuickStart() {
  return (
    <section style={{ padding: '4rem 0', background: 'var(--ifm-background-surface-color)' }}>
      <div className="container">
        <div className="row">
          <div className="col col--6">
            <Heading as="h2" style={{ marginBottom: '1rem' }}>
              Quick Start
            </Heading>
            <p style={{ fontSize: '1.125rem', color: 'var(--ifm-color-emphasis-700)', lineHeight: 1.7 }}>
              Get up and running in under a minute. Create your first FastAPI project with
              authentication, database migrations, and a clean architecture.
            </p>
            <Link
              className="button button--primary button--lg"
              to="/docs/getting-started/first-project"
              style={{ marginTop: '1rem' }}>
              Read the Tutorial →
            </Link>
          </div>
          <div className="col col--6">
            <div style={{
              background: '#1e293b',
              borderRadius: '0.5rem',
              padding: '1.5rem',
              fontFamily: 'var(--ifm-font-family-monospace)',
              fontSize: '0.9rem',
              lineHeight: 1.8
            }}>
              <div style={{ color: '#64748b' }}># Install Fastman</div>
              <div style={{ color: '#f8fafc' }}>pip install fastman</div>
              <div style={{ height: '1rem' }}></div>
              <div style={{ color: '#64748b' }}># Create a new project</div>
              <div style={{ color: '#f8fafc' }}>fastman new my-api --database=postgresql</div>
              <div style={{ height: '1rem' }}></div>
              <div style={{ color: '#64748b' }}># Start the server</div>
              <div style={{ color: '#f8fafc' }}>cd my-api && fastman serve</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title="The Elegant CLI for FastAPI"
      description="Laravel-inspired CLI tool for FastAPI. Generate projects, scaffold features, manage databases, and deploy with confidence.">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <QuickStart />
      </main>
    </Layout>
  );
}
