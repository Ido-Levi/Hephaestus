import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  image: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Semi-Structured Agent Framework',
    image: require('@site/static/img/semi_structured_framework.png').default,
    description: (
      <>
        Not rigid workflows that break when reality diverges. Not chaotic agents that
        duplicate work. Define phase types—analysis, building, validation—then let
        agents spawn tasks across any phase based on what they discover. Testing finds
        bugs? Spawn fixes. Validation spots optimizations? Spawn investigations.
        Workflows build themselves. Structure where you need it, flexibility everywhere else.
      </>
    ),
  },
  {
    title: 'Trajectory Analysis',
    image: require('@site/static/img/trajectory_analysis.png').default,
    description: (
      <>
        Guardian doesn't just check "is the agent stuck?" It analyzes entire conversation
        trajectories—is the accumulated work aligned with phase goals? LLM-powered
        coherence scoring evaluates whether agents are making meaningful progress toward
        objectives, not just completing tasks. Targeted interventions steer without
        micromanaging. Agents stay autonomous but aligned.
      </>
    ),
  },
  {
    title: 'Kanban Ticket Coordination',
    image: require('@site/static/img/kanban_coordination.png').default,
    description: (
      <>
        Tickets flow through your workflow carrying context. Created in analysis,
        implemented in building, validated in testing—one ticket follows a component
        through its entire lifecycle. Comments accumulate decisions, commits link to code
        changes, blocking relationships enforce dependencies. Coordination without
        central planning. The workflow coordinates itself.
      </>
    ),
  },
];

function Feature({title, image, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <img src={image} className={styles.featureSvg} alt={title} />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
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
