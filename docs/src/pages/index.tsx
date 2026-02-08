import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import {
  RocketLaunchIcon,
  CubeTransparentIcon,
  CircleStackIcon,
  ShieldCheckIcon,
  CommandLineIcon,
  BoltIcon,
} from '@heroicons/react/24/outline';

import styles from './index.module.css';

function BackgroundBlobs() {
  return (
    <div className={styles.blobContainer}>
      <div className={styles.blob1}></div>
      <div className={styles.blob2}></div>
      <div className={styles.blob3}></div>
    </div>
  );
}

function HomepageHeader() {
  return (
    <header className={styles.hero}>
      <BackgroundBlobs />
      <div className="container">
        <div className={styles.heroContent}>
          <div className={styles.badge}>
            <span>v0.3.0</span> Now Available
          </div>
          <Heading as="h1" className={styles.heroTitle}>
            The Elegant CLI for
            <span className={styles.gradient}> FastAPI </span>
            Artisans
          </Heading>
          <p className={styles.heroSubtitle}>
            Generate projects, scaffold features, manage databases, and deploy with confidence.
            Laravel-inspired developer experience for FastAPI.
          </p>
          <div className={styles.heroButtons}>
            <Link className={styles.primaryButton} to="/docs/intro">
              Get Started
              <svg className={styles.buttonIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
            <Link className={styles.secondaryButton} href="https://github.com/acathon/fastman-cli">
              <svg className={styles.githubIcon} viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
              View on GitHub
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}

type FeatureItem = {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  title: string;
  description: string;
  gradient: string;
};

const features: FeatureItem[] = [
  {
    icon: RocketLaunchIcon,
    title: 'Project Scaffolding',
    description: 'Create production-ready FastAPI projects with one command. Choose your architecture and database.',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  {
    icon: CubeTransparentIcon,
    title: 'Multiple Architectures',
    description: 'Feature-based vertical slices, API-versioned, or traditional layered patterns. You choose.',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  },
  {
    icon: CircleStackIcon,
    title: 'Database Ready',
    description: 'SQLite, PostgreSQL, MySQL, Oracle, Firebase. Migrations and seeders included.',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  },
  {
    icon: ShieldCheckIcon,
    title: 'Auth Scaffolding',
    description: 'JWT, OAuth, or Keycloak authentication. One command setup with best practices.',
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  },
  {
    icon: CommandLineIcon,
    title: 'Smart Detection',
    description: 'Auto-detects uv, poetry, pipenv, or pip. Works with your preferred package manager.',
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  },
  {
    icon: BoltIcon,
    title: 'Production Ready',
    description: 'Docker builds, config caching, code optimization. From development to deployment.',
    gradient: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  },
];

function Feature({ icon: Icon, title, description, gradient }: FeatureItem) {
  return (
    <div className={styles.featureCard}>
      <div className={styles.featureIconWrapper} style={{ background: gradient }}>
        <Icon className={styles.featureIcon} />
      </div>
      <Heading as="h3" className={styles.featureTitle}>
        {title}
      </Heading>
      <p className={styles.featureDescription}>
        {description}
      </p>
    </div>
  );
}

function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className={styles.featuresHeader}>
          <Heading as="h2" className={styles.sectionTitle}>
            Everything you need to build faster
          </Heading>
          <p className={styles.sectionSubtitle}>
            Fastman provides all the tools you need to build production-ready FastAPI applications.
          </p>
        </div>
        <div className={styles.featuresGrid}>
          {features.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}

function CodeExample() {
  return (
    <section className={styles.codeSection}>
      <div className="container">
        <div className={styles.codeWrapper}>
          <div className={styles.codeInfo}>
            <Heading as="h2" className={styles.codeTitle}>
              Get started in seconds
            </Heading>
            <p className={styles.codeDescription}>
              Create a production-ready FastAPI project with authentication,
              database migrations, and a clean architecture in just a few commands.
            </p>
            <Link className={styles.learnMoreLink} to="/docs/getting-started/first-project">
              Learn more
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </Link>
          </div>
          <div className={styles.terminal}>
            <div className={styles.terminalHeader}>
              <div className={styles.terminalDots}>
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className={styles.terminalTitle}>Terminal</span>
            </div>
            <div className={styles.terminalBody}>
              <div className={styles.terminalLine}>
                <span className={styles.prompt}>$</span>
                <span className={styles.command}>pip install fastman</span>
              </div>
              <div className={styles.terminalLine}>
                <span className={styles.prompt}>$</span>
                <span className={styles.command}>fastman new my-api --database=postgresql</span>
              </div>
              <div className={styles.terminalOutput}>
                <span className={styles.success}>✓</span> Creating project structure...
              </div>
              <div className={styles.terminalOutput}>
                <span className={styles.success}>✓</span> Installing dependencies...
              </div>
              <div className={styles.terminalOutput}>
                <span className={styles.success}>✓</span> Project created successfully!
              </div>
              <div className={styles.terminalLine}>
                <span className={styles.prompt}>$</span>
                <span className={styles.command}>cd my-api && fastman serve</span>
              </div>
              <div className={styles.terminalOutput}>
                <span className={styles.info}>→</span> Server running at http://localhost:8000
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section className={styles.cta}>
      <div className="container">
        <div className={styles.ctaContent}>
          <Heading as="h2" className={styles.ctaTitle}>
            Ready to build something amazing?
          </Heading>
          <p className={styles.ctaSubtitle}>
            Join developers who are building faster with Fastman.
          </p>
          <div className={styles.ctaButtons}>
            <Link className={styles.ctaPrimary} to="/docs/intro">
              Get Started for Free
            </Link>
            <Link className={styles.ctaSecondary} href="https://github.com/acathon/fastman-cli">
              Star on GitHub
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <Layout
      title="The Elegant CLI for FastAPI"
      description="Laravel-inspired CLI tool for FastAPI. Generate projects, scaffold features, manage databases, and deploy with confidence.">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <CodeExample />
        <CTASection />
      </main>
    </Layout>
  );
}
