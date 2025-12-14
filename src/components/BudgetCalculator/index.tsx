import React, { useState, useEffect, useMemo } from 'react';

// Hardware component interfaces
interface HardwareComponent {
  id: string;
  name: string;
  category: 'compute' | 'sensors' | 'actuators' | 'power' | 'storage' | 'accessories';
  basePrice: number;
  description: string;
  specifications: Record<string, string>;
  alternatives?: HardwareComponent[];
}

interface HardwareTier {
  id: string;
  name: string;
  description: string;
  totalPrice: number;
  components: HardwareComponent[];
  recommendedFor: string[];
}

interface CloudInstance {
  id: string;
  name: string;
  provider: string;
  hourlyRate: number;
  compute: string;
  memory: string;
  storage: string;
  gpu?: string;
  description: string;
}

interface CostProjection {
  monthly: number;
  annual: number;
  threeYear: number;
}

interface BudgetConfiguration {
  selectedTier: string;
  selectedCloudInstance: string | null;
  customComponents: Record<string, number>;
  quantity: Record<string, number>;
  usageHours: number;
  cloudUsageHours: number;
  includeMaintenance: boolean;
  includeTraining: boolean;
  includeSoftware: boolean;
}

interface OptimizationRecommendation {
  type: 'cost-saving' | 'performance' | 'scalability';
  title: string;
  description: string;
  potentialSavings: number;
  implementation: string;
}

const BudgetCalculator: React.FC = () => {
  // Hardware tiers data
  const hardwareTiers: HardwareTier[] = [
    {
      id: 'edge-kit',
      name: 'Edge Kit',
      description: 'Basic setup for edge AI development and learning',
      totalPrice: 700,
      recommendedFor: ['Beginners', 'Students', 'Edge AI projects'],
      components: [
        {
          id: 'jetson-orin-nano',
          name: 'NVIDIA Jetson Orin Nano',
          category: 'compute',
          basePrice: 499,
          description: 'Compact AI computer with 40 TOPS performance',
          specifications: {
            'AI Performance': '40 TOPS',
            'Memory': '8GB LPDDR5',
            'Storage': 'microSD (up to 1TB)',
            'Power': '10W'
          }
        },
        {
          id: 'realsense-d435i',
          name: 'Intel RealSense D435i',
          category: 'sensors',
          basePrice: 199,
          description: 'Depth camera with inertial measurement unit',
          specifications: {
            'Depth Resolution': '1280x720',
            'Frame Rate': '30 fps',
            'Range': '0.2m - 10m',
            'IMU': '6-axis accelerometer + gyro'
          }
        }
      ]
    },
    {
      id: 'proxy-robot',
      name: 'Proxy Robot',
      description: 'Mid-range robot for advanced development',
      totalPrice: 2400,
      recommendedFor: ['Advanced students', 'Research', 'Prototype development'],
      components: [
        {
          id: 'rtx-4060',
          name: 'NVIDIA RTX 4060 GPU',
          category: 'compute',
          basePrice: 400,
          description: 'High-performance GPU for AI workloads',
          specifications: {
            'CUDA Cores': '3072',
            'Memory': '8GB GDDR6',
            'AI Performance': '231 TOPS',
            'Power': '200W'
          }
        },
        {
          id: 'rpi-5',
          name: 'Raspberry Pi 5',
          category: 'compute',
          basePrice: 80,
          description: 'Single-board computer for control tasks',
          specifications: {
            'CPU': 'ARM Cortex-A76',
            'Memory': '8GB LPDDR4X',
            'Storage': 'microSD + NVMe',
            'Power': '12W'
          }
        },
        {
          id: 'dynamixel-servos',
          name: 'Robotis Dynamixel Servos',
          category: 'actuators',
          basePrice: 900,
          description: 'Set of smart servos for robot movement',
          specifications: {
            'Quantity': '6x XM430',
            'Torque': '4.1 Nm',
            'Control': 'Position/Velocity/Current',
            'Interface': 'TTL'
          }
        },
        {
          id: 'lidar-lite',
          name: 'LIDAR-Lite v4',
          category: 'sensors',
          basePrice: 150,
          description: 'Compact laser rangefinder',
          specifications: {
            'Range': '0.05m - 40m',
            'Accuracy': '±2.5cm',
            'Update Rate': '100Hz',
            'Interface': 'I2C/UART'
          }
        },
        {
          id: 'power-distribution',
          name: 'Power Distribution Unit',
          category: 'power',
          basePrice: 120,
          description: 'Power management and distribution',
          specifications: {
            'Input': '12V 10A',
            'Outputs': '5x regulated',
            'Protection': 'Overcurrent/overvoltage',
            'Monitoring': 'Current/voltage'
          }
        },
        {
          id: 'robot-frame',
          name: 'Robot Frame Kit',
          category: 'accessories',
          basePrice: 750,
          description: 'Aluminum robot chassis and mounting hardware',
          specifications: {
            'Material': '6061 Aluminum',
            'Size': '50x40x60 cm',
            'Weight': '8kg',
            'Modularity': 'Customizable'
          }
        }
      ]
    },
    {
      id: 'premium-lab',
      name: 'Premium Lab',
      description: 'Complete professional development setup',
      totalPrice: 16500,
      recommendedFor: ['Professional development', 'Advanced research', 'Production systems'],
      components: [
        {
          id: 'rtx-5090',
          name: 'NVIDIA RTX 5090',
          category: 'compute',
          basePrice: 2000,
          description: 'Top-tier GPU for maximum AI performance',
          specifications: {
            'CUDA Cores': '16384',
            'Memory': '24GB GDDR7',
            'AI Performance': '1979 TOPS',
            'Power': '450W'
          }
        },
        {
          id: 'threadripper-pro',
          name: 'AMD Threadripper PRO 7975WX',
          category: 'compute',
          basePrice: 4000,
          description: 'High-end workstation CPU',
          specifications: {
            'Cores': '32 cores / 64 threads',
            'Base Clock': '3.2GHz',
            'Max Boost': '5.1GHz',
            'Cache': '128MB L3'
          }
        },
        {
          id: '64gb-ddr5',
          name: '64GB DDR5 RAM',
          category: 'storage',
          basePrice: 500,
          description: 'High-speed memory for large datasets',
          specifications: {
            'Capacity': '64GB',
            'Type': 'DDR5-5600',
            'Channels': 'Quad-channel',
            'ECC': 'Supported'
          }
        },
        {
          id: 'nvme-4tb',
          name: '4TB NVMe SSD',
          category: 'storage',
          basePrice: 300,
          description: 'Ultra-fast storage for OS and datasets',
          specifications: {
            'Capacity': '4TB',
            'Interface': 'PCIe 4.0',
            'Read Speed': '7000 MB/s',
            'Write Speed': '6000 MB/s'
          }
        },
        {
          id: 'ouster-lidar',
          name: 'Ouster OS0-128',
          category: 'sensors',
          basePrice: 8000,
          description: 'High-resolution digital LiDAR',
          specifications: {
            'Channels': '128',
            'Range': '120m',
            'Rate': '10-20 Hz',
            'Accuracy': '±2cm'
          }
        },
        {
          id: 'rea-robot-arm',
          name: 'Robot Arm 6-DOF',
          category: 'actuators',
          basePrice: 1200,
          description: 'Six-degree-of-freedom robotic arm',
          specifications: {
            'DOF': '6',
            'Payload': '5kg',
            'Reach': '850mm',
            'Repeatability': '±0.05mm'
          }
        },
        {
          id: 'motion-capture',
          name: 'Motion Capture System',
          category: 'sensors',
          basePrice: 500,
          description: 'Full-body motion tracking',
          specifications: {
            'Cameras': '8x 1080p',
            'Frame Rate': '120 fps',
            'Tracking': 'Full body',
            'Latency': '<10ms'
          }
        }
      ]
    }
  ];

  // Cloud instances data
  const cloudInstances: CloudInstance[] = [
    {
      id: 'aws-g5-2xlarge',
      name: 'AWS g5.2xlarge',
      provider: 'AWS',
      hourlyRate: 1.212,
      compute: '1 GPU + 8 vCPUs',
      memory: '32 GB',
      storage: 'EBS up to 8TB',
      gpu: 'NVIDIA A10G',
      description: 'GPU instance for AI training and inference'
    },
    {
      id: 'aws-g5-12xlarge',
      name: 'AWS g5.12xlarge',
      provider: 'AWS',
      hourlyRate: 7.272,
      compute: '4 GPUs + 48 vCPUs',
      memory: '192 GB',
      storage: 'EBS up to 8TB',
      gpu: '4x NVIDIA A10G',
      description: 'Multi-GPU instance for large-scale training'
    },
    {
      id: 'azure-nc6s-v3',
      name: 'Azure NC6s_v3',
      provider: 'Azure',
      hourlyRate: 3.06,
      compute: '1 GPU + 6 vCPUs',
      memory: '112 GB',
      storage: '736 GB SSD',
      gpu: 'NVIDIA V100',
      description: 'High-memory GPU instance'
    },
    {
      id: 'gcp-a2-highgpu',
      name: 'GCP A2-highgpu',
      provider: 'GCP',
      hourlyRate: 4.16,
      compute: '1 GPU + 12 vCPUs',
      memory: '170 GB',
      storage: '1.7 TB SSD',
      gpu: 'NVIDIA A100',
      description: 'A100 GPU for cutting-edge AI'
    }
  ];

  // State management
  const [config, setConfig] = useState<BudgetConfiguration>({
    selectedTier: 'edge-kit',
    selectedCloudInstance: null,
    customComponents: {},
    quantity: {},
    usageHours: 160, // Monthly usage hours
    cloudUsageHours: 160,
    includeMaintenance: true,
    includeTraining: false,
    includeSoftware: true
  });

  const [showComparison, setShowComparison] = useState(false);
  const [showOptimizations, setShowOptimizations] = useState(false);

  // Calculate hardware costs
  const calculateHardwareCosts = useMemo(() => {
    const selectedTier = hardwareTiers.find(t => t.id === config.selectedTier);
    if (!selectedTier) return 0;

    let baseCost = selectedTier.totalPrice;

    // Add custom components
    Object.entries(config.customComponents).forEach(([componentId, quantity]) => {
      const component = selectedTier.components.find(c => c.id === componentId);
      if (component) {
        baseCost += component.basePrice * quantity;
      }
    });

    // Apply quantity adjustments
    if (config.quantity[config.selectedTier]) {
      baseCost *= config.quantity[config.selectedTier];
    }

    // Add additional costs
    if (config.includeMaintenance) {
      baseCost += selectedTier.totalPrice * 0.15; // 15% annual maintenance
    }

    if (config.includeTraining) {
      baseCost += 2000; // Training costs
    }

    if (config.includeSoftware) {
      baseCost += 1000; // Software licenses
    }

    return baseCost;
  }, [config]);

  // Calculate cloud costs
  const calculateCloudCosts = useMemo(() => {
    if (!config.selectedCloudInstance) return 0;

    const instance = cloudInstances.find(i => i.id === config.selectedCloudInstance);
    if (!instance) return 0;

    const monthlyCost = instance.hourlyRate * config.cloudUsageHours;
    return {
      monthly: monthlyCost,
      annual: monthlyCost * 12,
      threeYear: monthlyCost * 36
    };
  }, [config.selectedCloudInstance, config.cloudUsageHours]);

  // Generate cost projections
  const generateProjections = useMemo((): CostProjection => {
    const hardwareMonthly = calculateHardwareCosts / 12; // Annualized
    const cloudMonthly = calculateCloudCosts.monthly || 0;

    const totalMonthly = hardwareMonthly + cloudMonthly;
    const totalAnnual = totalMonthly * 12;
    const totalThreeYear = totalAnnual * 3;

    return {
      monthly: totalMonthly,
      annual: totalAnnual,
      threeYear: totalThreeYear
    };
  }, [calculateHardwareCosts, calculateCloudCosts]);

  // Generate optimization recommendations
  const generateRecommendations = useMemo((): OptimizationRecommendation[] => {
    const recommendations: OptimizationRecommendation[] = [];

    if (config.selectedTier === 'premium-lab' && config.cloudUsageHours < 100) {
      recommendations.push({
        type: 'cost-saving',
        title: 'Optimize Cloud Usage',
        description: 'Your cloud usage is minimal. Consider spot instances or reserved instances for better pricing.',
        potentialSavings: calculateCloudCosts.monthly * 0.3,
        implementation: 'Switch to AWS Reserved Instances or use Spot Instances for non-critical workloads'
      });
    }

    if (config.selectedTier === 'proxy-robot' && !config.cloudUsageHours) {
      recommendations.push({
        type: 'performance',
        title: 'Add Cloud GPU Access',
        description: 'Enhance your Proxy Robot with cloud GPU for heavy AI tasks.',
        potentialSavings: 0,
        implementation: 'Integrate AWS g5.2xlarge for training while keeping local inference'
      });
    }

    if (calculateHardwareCosts > 10000 && !config.includeMaintenance) {
      recommendations.push({
        type: 'scalability',
        title: 'Add Maintenance Plan',
        description: 'Protect your investment with proper maintenance.',
        potentialSavings: calculateHardwareCosts * 0.1,
        implementation: 'Schedule regular maintenance and component upgrades'
      });
    }

    return recommendations;
  }, [config, calculateHardwareCosts, calculateCloudCosts]);

  // Export functions
  const exportToCSV = () => {
    const data = [
      ['Configuration', 'Value'],
      ['Selected Tier', config.selectedTier],
      ['Hardware Cost', `$${calculateHardwareCosts.toFixed(2)}`],
      ['Monthly Projection', `$${generateProjections.monthly.toFixed(2)}`],
      ['Annual Projection', `$${generateProjections.annual.toFixed(2)}`],
      ['3-Year Projection', `$${generateProjections.threeYear.toFixed(2)}`]
    ];

    if (config.selectedCloudInstance) {
      data.push(['Cloud Instance', config.selectedCloudInstance]);
      data.push(['Monthly Cloud Cost', `$${calculateCloudCosts.monthly.toFixed(2)}`]);
    }

    const csvContent = data.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'budget-calculator-export.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportToJSON = () => {
    const exportData = {
      configuration: config,
      costs: {
        hardware: calculateHardwareCosts,
        cloud: calculateCloudCosts,
        projections: generateProjections
      },
      recommendations: generateRecommendations,
      timestamp: new Date().toISOString()
    };

    const jsonContent = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'budget-calculator-export.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Component JSX
  return (
    <div className="w-full max-w-6xl mx-auto p-6 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 rounded-lg shadow-lg border border-zinc-200 dark:border-zinc-700">
      {/* Tier Selection */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
          Select Hardware Tier
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {hardwareTiers.map(tier => (
            <div
              key={tier.id}
              className={`p-4 border rounded-lg cursor-pointer transition-all ${
                config.selectedTier === tier.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-zinc-200 dark:border-zinc-700 hover:border-zinc-300'
              }`}
              onClick={() => setConfig(prev => ({ ...prev, selectedTier: tier.id }))}
            >
              <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
                {tier.name}
              </h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                {tier.description}
              </p>
              <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                ${tier.totalPrice.toLocaleString()}
              </p>
              <div className="mt-2">
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Recommended for:
                </p>
                {tier.recommendedFor.map((rec, idx) => (
                  <span
                    key={idx}
                    className="inline-block px-2 py-1 text-xs bg-zinc-100 dark:bg-zinc-800 rounded mr-1 mb-1"
                  >
                    {rec}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Configuration Options */}
      <div className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
            Configuration Options
          </h3>

          <div className="space-y-4">
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={config.includeMaintenance}
                  onChange={e => setConfig(prev => ({
                    ...prev,
                    includeMaintenance: e.target.checked
                  }))}
                  className="mr-2"
                />
                <span className="text-sm text-zinc-700 dark:text-zinc-300">
                  Include Maintenance (15% annually)
                </span>
              </label>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={config.includeTraining}
                  onChange={e => setConfig(prev => ({
                    ...prev,
                    includeTraining: e.target.checked
                  }))}
                  className="mr-2"
                />
                <span className="text-sm text-zinc-700 dark:text-zinc-300">
                  Include Training ($2,000)
                </span>
              </label>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={config.includeSoftware}
                  onChange={e => setConfig(prev => ({
                    ...prev,
                    includeSoftware: e.target.checked
                  }))}
                  className="mr-2"
                />
                <span className="text-sm text-zinc-700 dark:text-zinc-300">
                  Include Software Licenses ($1,000)
                </span>
              </label>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
            Quantity
          </h3>

          <div>
            <label className="block text-sm text-zinc-700 dark:text-zinc-300 mb-2">
              Number of Setups
            </label>
            <input
              type="number"
              min="1"
              value={config.quantity[config.selectedTier] || 1}
              onChange={e => setConfig(prev => ({
                ...prev,
                quantity: {
                  ...prev.quantity,
                  [prev.selectedTier]: parseInt(e.target.value) || 1
                }
              }))}
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:ring-2 focus:ring-[#10a37f] focus:border-transparent outline-none transition-colors"
            />
          </div>
        </div>
      </div>

      {/* Selected Tier Components */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
          Included Components
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {hardwareTiers
            .find(t => t.id === config.selectedTier)
            ?.components.map(component => (
              <div
                key={component.id}
                className="p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg"
              >
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {component.name}
                  </h4>
                  <span className="text-sm font-bold text-zinc-700 dark:text-zinc-300">
                    ${component.basePrice.toLocaleString()}
                  </span>
                </div>
                <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                  {component.description}
                </p>
                <div className="text-xs text-zinc-500 dark:text-zinc-400">
                  {Object.entries(component.specifications).map(([key, value]) => (
                    <div key={key}>
                      <span className="font-medium">{key}:</span> {value}
                    </div>
                  ))}
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Cloud Instance Selection */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
          Cloud Alternatives (Optional)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {cloudInstances.map(instance => (
            <div
              key={instance.id}
              className={`p-4 border rounded-lg cursor-pointer transition-all ${
                config.selectedCloudInstance === instance.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-zinc-200 dark:border-zinc-700 hover:border-zinc-300'
              }`}
              onClick={() => setConfig(prev => ({
                ...prev,
                selectedCloudInstance: instance.id
              }))}
            >
              <h4 className="font-semibold text-zinc-900 dark:text-zinc-100">
                {instance.name}
              </h4>
              <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                {instance.description}
              </p>
              <p className="text-lg font-bold text-green-600 dark:text-green-400">
                ${instance.hourlyRate.toFixed(3)}/hour
              </p>
              <div className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                <div>{instance.compute}</div>
                <div>{instance.memory} RAM</div>
                <div>{instance.storage}</div>
                {instance.gpu && <div>{instance.gpu}</div>}
              </div>
            </div>
          ))}
        </div>

        {config.selectedCloudInstance && (
          <div>
            <label className="block text-sm text-zinc-700 dark:text-zinc-300 mb-2">
              Monthly Usage Hours
            </label>
            <input
              type="number"
              min="0"
              max="744"
              value={config.cloudUsageHours}
              onChange={e => setConfig(prev => ({
                ...prev,
                cloudUsageHours: parseInt(e.target.value) || 0
              }))}
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:ring-2 focus:ring-[#10a37f] focus:border-transparent outline-none transition-colors"
            />
          </div>
        )}
      </div>

      {/* Cost Summary */}
      <div className="mb-8 p-6 bg-zinc-50 dark:bg-zinc-800 rounded-lg">
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
          Cost Summary
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-1">
              Hardware Cost (One-time)
            </p>
            <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
              ${calculateHardwareCosts.toLocaleString()}
            </p>
          </div>

          <div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-1">
              Monthly Total
            </p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              ${generateProjections.monthly.toFixed(2)}
            </p>
          </div>

          <div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-1">
              Annual Projection
            </p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              ${generateProjections.annual.toFixed(2)}
            </p>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700">
          <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-1">
            3-Year Projection
          </p>
          <p className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
            ${generateProjections.threeYear.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Comparison Dropdown */}
      <div className="mb-8 border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
        <button
          onClick={() => setShowComparison(!showComparison)}
          className="w-full flex justify-between items-center p-4 bg-zinc-100 dark:bg-zinc-800 text-left hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
        >
          <span className="font-semibold text-zinc-900 dark:text-zinc-100">Cloud vs On-Premise Comparison</span>
          <svg
            className={`w-5 h-5 text-zinc-500 transform transition-transform ${showComparison ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        {showComparison && (
          <div className="p-6 bg-zinc-50 dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-700">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800">
                <h4 className="font-semibold text-zinc-800 dark:text-zinc-200 mb-3">
                  On-Premise (Hardware)
                </h4>
                <ul className="space-y-2 text-sm text-zinc-600 dark:text-zinc-400">
                  <li className="flex items-start">
                    <span className="text-[#10a37f] mr-2">✓</span>
                    Full control over hardware
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#10a37f] mr-2">✓</span>
                    No recurring monthly costs
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#10a37f] mr-2">✓</span>
                    Complete data privacy
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#10a37f] mr-2">✓</span>
                    Customizable and upgradable
                  </li>
                  <li className="flex items-start">
                    <span className="text-red-500 mr-2">✗</span>
                    High upfront investment
                  </li>
                  <li className="flex items-start">
                    <span className="text-red-500 mr-2">✗</span>
                    Maintenance required
                  </li>
                </ul>
              </div>

              <div className="p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800">
                <h4 className="font-semibold text-zinc-800 dark:text-zinc-200 mb-3">
                  Cloud Computing
                </h4>
                <ul className="space-y-2 text-sm text-zinc-600 dark:text-zinc-400">
                  <li className="flex items-start">
                    <span className="text-[#10a37f] mr-2">✓</span>
                    Pay-as-you-go pricing
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#10a37f] mr-2">✓</span>
                    No hardware maintenance
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#10a37f] mr-2">✓</span>
                    Access to latest GPUs
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#10a37f] mr-2">✓</span>
                    Scalable resources
                  </li>
                  <li className="flex items-start">
                    <span className="text-red-500 mr-2">✗</span>
                    Recurring monthly costs
                  </li>
                  <li className="flex items-start">
                    <span className="text-red-500 mr-2">✗</span>
                    Data transfer costs
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Optimization Recommendations Dropdown */}
      <div className="mb-8 border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
        <button
          onClick={() => setShowOptimizations(!showOptimizations)}
          className="w-full flex justify-between items-center p-4 bg-zinc-100 dark:bg-zinc-800 text-left hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
        >
          <span className="font-semibold text-zinc-900 dark:text-zinc-100">Optimization Recommendations</span>
          <svg
            className={`w-5 h-5 text-zinc-500 transform transition-transform ${showOptimizations ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {showOptimizations && (
          <div className="p-6 bg-zinc-50 dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-700">
            {generateRecommendations.length > 0 ? (
              <div className="space-y-4">
                {generateRecommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-zinc-900 dark:text-zinc-100">
                        {rec.title}
                      </h4>
                      <span className={`px-2 py-1 text-xs rounded ${
                        rec.type === 'cost-saving'
                          ? 'bg-[#10a37f]/10 text-[#10a37f]'
                          : rec.type === 'performance'
                          ? 'bg-[#10a37f]/10 text-[#10a37f]'
                          : 'bg-[#10a37f]/10 text-[#10a37f]'
                      }`}>
                        {rec.type}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                      {rec.description}
                    </p>
                    {rec.potentialSavings > 0 && (
                      <p className="text-sm font-semibold text-[#10a37f] mb-2">
                        Potential Savings: ${rec.potentialSavings.toFixed(2)}
                      </p>
                    )}
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">
                      <strong>Implementation:</strong> {rec.implementation}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Your current configuration is well-optimized! No specific recommendations at this time.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Export Options */}
      <div className="flex flex-col sm:flex-row gap-4 justify-end mt-8 pt-6 border-t border-zinc-200 dark:border-zinc-700">
        <button
          onClick={exportToCSV}
          className="px-6 py-2 bg-[#10a37f] text-white rounded-lg hover:bg-[#0d8f6c] transition-colors w-full sm:w-auto"
        >
          Export to CSV
        </button>
        <button
          onClick={exportToJSON}
          className="px-6 py-2 bg-[#10a37f] text-white rounded-lg hover:bg-[#0d8f6c] transition-colors w-full sm:w-auto"
        >
          Export to JSON
        </button>
      </div>
    </div>
  );
};

export default BudgetCalculator;