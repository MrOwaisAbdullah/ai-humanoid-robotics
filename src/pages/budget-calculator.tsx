import React from 'react';
import Layout from '@theme/Layout';
import BudgetCalculator from '@site/src/components/BudgetCalculator';

export default function BudgetCalculatorPage(): React.JSX.Element {
  return (
    <Layout
      title="Budget Calculator"
      description="Plan your Physical AI & Humanoid Robotics hardware setup with our comprehensive budget calculator"
    >
      <main className="container margin-vert--lg">
        <BudgetCalculator />
      </main>
    </Layout>
  );
}