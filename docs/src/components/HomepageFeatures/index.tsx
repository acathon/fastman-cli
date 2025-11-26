import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg?: React.ComponentType<React.ComponentProps<'svg'>>;
  description: JSX.Element;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Zero Boilerplate',
    description: (
      <>
        Stop writing the same setup code. Fastman generates routers, models, schemas, and services instantly.
      </>
    ),
  },
  {
    title: 'Multiple Architectures',
    description: (
      <>
        Choose between Vertical Slice (Feature), Layered (MVC), or simple API patterns. Fastman adapts to your style.
      </>
    ),
  },
  {
    title: 'Database Ready',
    description: (
      <>
        First-class support for SQLite, PostgreSQL, MySQL, and Oracle. Migrations are handled via simple CLI commands.
      </>
    ),
  },
  {
    title: 'Auth Scaffolding',
    description: (
      <>
        Secure your app in seconds. Scaffold JWT or Keycloak authentication with a single command.
      </>
    ),
  },
  {
    title: 'Interactive Shell',
    description: (
      <>
        Debug with ease using the `tinker` command. Access your app context and database models in a REPL.
      </>
    ),
  },
  {
    title: 'Smart Tooling',
    description: (
      <>
        Automatically detects your package manager (uv, poetry, pip) and optimizes your imports.
      </>
    ),
  },
];

function Feature({ title, Svg, description }: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        {/* <Svg className={styles.featureSvg} role="img" /> */}
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): JSX.Element {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
