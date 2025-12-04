import React from 'react';
import HardwareComparison, { HardwareComparisonContainer } from './index';

const HardwareComparisonDemo: React.FC = () => {
  // Example handler for BudgetCalculator integration
  const handleComponentsUpdate = (components: Record<string, any>) => {
    console.log('Selected components for budget:', components);

    // Calculate total price
    const totalPrice = Object.values(components).reduce((sum: number, comp: any) => sum + comp.basePrice, 0);
    console.log(`Total estimated price: $${totalPrice}`);

    // Here you would typically update state or pass to a budget calculation component
    alert(`Components selected! Total: $${totalTotalPrice}`);
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-900 dark:text-white">
          Hardware Comparison Tool Demo
        </h1>

        {/* Basic Hardware Comparison (Standalone) */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200">
            Standalone Hardware Comparison
          </h2>
          <p className="mb-4 text-gray-600 dark:text-gray-400">
            Compare hardware components across different tiers with filtering, sorting, and export capabilities.
          </p>
          <HardwareComparison />
        </section>

        {/* Integrated Hardware Comparison (with Budget Calculator) */}
        <section>
          <h2 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200">
            Integrated with Budget Calculator
          </h2>
          <p className="mb-4 text-gray-600 dark:text-gray-400">
            Select components to add them to your budget configuration. The system will calculate total costs and provide ROI projections.
          </p>
          <HardwareComparisonContainer onComponentsUpdate={handleComponentsUpdate} />
        </section>

        {/* Usage Instructions */}
        <section className="mt-12 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200">
            How to Use
          </h2>
          <ol className="list-decimal list-inside space-y-2 text-gray-600 dark:text-gray-400">
            <li>Select a component category (GPU, CPU, RAM, Storage, or Sensors)</li>
            <li>Use filters to narrow down options by tier and price range</li>
            <li>Sort components by price, performance, name, or tier</li>
            <li>View detailed specifications for each component</li>
            <li>Compare price-to-performance ratios with visual indicators</li>
            <li>Export comparison data to CSV or JSON formats</li>
            <li>In integrated mode, click "Add to Budget" to include in your configuration</li>
          </ol>
        </section>
      </div>
    </div>
  );
};

export default HardwareComparisonDemo;