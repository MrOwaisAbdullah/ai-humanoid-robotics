import React, { useState, useMemo, useCallback } from 'react';

// Hardware specification interfaces
interface GPUSpec {
  model: string;
  tier: 'edge' | 'mid' | 'premium';
  price: number;
  cudaCores: number;
  tensorCores: number;
  memory: number;
  memoryType: string;
  memoryBandwidth: number;
  tflopsFP32: number;
  tflopsFP16: number;
  tensorTOPS: number;
  powerConsumption: number;
  dlssSupport?: boolean;
  rayTracingCores?: number;
}

interface CPUSpec {
  model: string;
  tier: 'edge' | 'mid' | 'premium';
  price: number;
  cores: number;
  threads: number;
  baseClock: number;
  boostClock: number;
  tdp: number;
  architecture: string;
  socket: string;
  cache: string;
}

interface RAMSpec {
  model: string;
  tier: 'edge' | 'mid' | 'premium';
  price: number;
  capacity: number;
  speed: number;
  type: 'DDR4' | 'DDR5' | 'LPDDR5';
  latency: number;
  modules: number;
  pricePerGB: number;
}

interface StorageSpec {
  model: string;
  tier: 'edge' | 'mid' | 'premium';
  price: number;
  capacity: number;
  type: 'NVMe' | 'SATA' | 'microSD';
  interface: string;
  readSpeed: number;
  writeSpeed: number;
  endurance: number;
  pricePerGB: number;
}

interface SensorSpec {
  model: string;
  tier: 'edge' | 'mid' | 'premium';
  price: number;
  type: 'camera' | 'lidar' | 'imu' | 'other';
  resolution?: string;
  range?: number;
  accuracy?: string;
  frameRate?: number;
  fov?: number;
  protocols: string[];
}

interface PerformanceBenchmark {
  category: 'simulation' | 'inference' | 'rendering' | 'training';
  metric: string;
  edgeValue: number;
  midValue: number;
  premiumValue: number;
  unit: string;
}

interface FilterOptions {
  tier: 'all' | 'edge' | 'mid' | 'premium';
  category: 'all' | 'gpu' | 'cpu' | 'ram' | 'storage' | 'sensors';
  maxPrice: number;
  minPerformance: number;
}

type SortField = 'price' | 'performance' | 'name' | 'tier';
type SortOrder = 'asc' | 'desc';

interface HardwareComparisonProps {
  onComponentSelect?: (component: any, category: string) => void;
  selectedComponents?: Record<string, any>;
}

const HardwareComparison: React.FC<HardwareComparisonProps> = ({
  onComponentSelect,
  selectedComponents = {}
}) => {
  // Hardware data
  const gpuData: GPUSpec[] = [
    {
      model: 'Jetson Orin Nano',
      tier: 'edge',
      price: 499,
      cudaCores: 1024,
      tensorCores: 32,
      memory: 8,
      memoryType: 'LPDDR5',
      memoryBandwidth: 68,
      tflopsFP32: 0.5,
      tflopsFP16: 10,
      tensorTOPS: 40,
      powerConsumption: 10
    },
    {
      model: 'RTX 4060 Ti',
      tier: 'mid',
      price: 399,
      cudaCores: 4352,
      tensorCores: 136,
      memory: 8,
      memoryType: 'GDDR6',
      memoryBandwidth: 288,
      tflopsFP32: 22.1,
      tflopsFP16: 44.2,
      tensorTOPS: 353,
      powerConsumption: 165,
      dlssSupport: true,
      rayTracingCores: 48
    },
    {
      model: 'RTX 4070 Ti',
      tier: 'mid',
      price: 799,
      cudaCores: 7680,
      tensorCores: 240,
      memory: 12,
      memoryType: 'GDDR6X',
      memoryBandwidth: 504,
      tflopsFP32: 40.1,
      tflopsFP16: 80.2,
      tensorTOPS: 641,
      powerConsumption: 285,
      dlssSupport: true,
      rayTracingCores: 60
    },
    {
      model: 'RTX 4090',
      tier: 'premium',
      price: 1599,
      cudaCores: 16384,
      tensorCores: 512,
      memory: 24,
      memoryType: 'GDDR6X',
      memoryBandwidth: 1008,
      tflopsFP32: 82.6,
      tflopsFP16: 165.2,
      tensorTOPS: 1321,
      powerConsumption: 450,
      dlssSupport: true,
      rayTracingCores: 128
    },
    {
      model: 'RTX 5090',
      tier: 'premium',
      price: 1999,
      cudaCores: 21760,
      tensorCores: 680,
      memory: 32,
      memoryType: 'GDDR7',
      memoryBandwidth: 1792,
      tflopsFP32: 125.4,
      tflopsFP16: 250.8,
      tensorTOPS: 2006,
      powerConsumption: 575,
      dlssSupport: true,
      rayTracingCores: 170
    }
  ];

  const cpuData: CPUSpec[] = [
    {
      model: 'Intel Core i5-13400',
      tier: 'edge',
      price: 215,
      cores: 6,
      threads: 12,
      baseClock: 2.5,
      boostClock: 4.6,
      tdp: 65,
      architecture: 'Raptor Lake',
      socket: 'LGA 1700',
      cache: '20MB'
    },
    {
      model: 'AMD Ryzen 7 7700X',
      tier: 'mid',
      price: 349,
      cores: 8,
      threads: 16,
      baseClock: 4.2,
      boostClock: 5.4,
      tdp: 105,
      architecture: 'Zen 4',
      socket: 'AM5',
      cache: '40MB'
    },
    {
      model: 'Intel Core i9-14900K',
      tier: 'premium',
      price: 589,
      cores: 24,
      threads: 32,
      baseClock: 2.1,
      boostClock: 6.0,
      tdp: 125,
      architecture: 'Raptor Lake Refresh',
      socket: 'LGA 1700',
      cache: '68MB'
    },
    {
      model: 'AMD Threadripper PRO 7965WX',
      tier: 'premium',
      price: 2499,
      cores: 24,
      threads: 48,
      baseClock: 3.2,
      boostClock: 5.3,
      tdp: 350,
      architecture: 'Zen 4',
      socket: 'sWRX8',
      cache: '154MB'
    }
  ];

  const ramData: RAMSpec[] = [
    {
      model: 'Corsair Vengeance LPX 16GB',
      tier: 'edge',
      price: 45,
      capacity: 16,
      speed: 3200,
      type: 'DDR4',
      latency: 16,
      modules: 2,
      pricePerGB: 2.81
    },
    {
      model: 'G.Skill Trident Z5 32GB',
      tier: 'mid',
      price: 149,
      capacity: 32,
      speed: 6000,
      type: 'DDR5',
      latency: 30,
      modules: 2,
      pricePerGB: 4.66
    },
    {
      model: 'Corsair Dominator Platinum RGB 64GB',
      tier: 'premium',
      price: 349,
      capacity: 64,
      speed: 6400,
      type: 'DDR5',
      latency: 32,
      modules: 4,
      pricePerGB: 5.45
    },
    {
      model: 'G.Skill Trident Z5 128GB',
      tier: 'premium',
      price: 699,
      capacity: 128,
      speed: 6800,
      type: 'DDR5',
      latency: 34,
      modules: 4,
      pricePerGB: 5.46
    }
  ];

  const storageData: StorageSpec[] = [
    {
      model: 'Samsung 970 EVO Plus 500GB',
      tier: 'edge',
      price: 59,
      capacity: 500,
      type: 'NVMe',
      interface: 'PCIe 3.0',
      readSpeed: 3500,
      writeSpeed: 3200,
      endurance: 600,
      pricePerGB: 0.12
    },
    {
      model: 'Samsung 980 PRO 2TB',
      tier: 'mid',
      price: 179,
      capacity: 2000,
      type: 'NVMe',
      interface: 'PCIe 4.0',
      readSpeed: 7000,
      writeSpeed: 5000,
      endurance: 1200,
      pricePerGB: 0.09
    },
    {
      model: 'Samsung 990 PRO 4TB',
      tier: 'premium',
      price: 349,
      capacity: 4000,
      type: 'NVMe',
      interface: 'PCIe 4.0',
      readSpeed: 7450,
      writeSpeed: 6900,
      endurance: 2400,
      pricePerGB: 0.09
    },
    {
      model: 'Crucial MX500 4TB',
      tier: 'premium',
      price: 249,
      capacity: 4000,
      type: 'SATA',
      interface: 'SATA III',
      readSpeed: 560,
      writeSpeed: 510,
      endurance: 700,
      pricePerGB: 0.06
    }
  ];

  const sensorData: SensorSpec[] = [
    {
      model: 'Intel RealSense D435i',
      tier: 'edge',
      price: 199,
      type: 'camera',
      resolution: '1920x1080',
      frameRate: 30,
      fov: 87,
      protocols: ['USB 3.0', 'ROS 2']
    },
    {
      model: 'OAK-D Lite',
      tier: 'mid',
      price: 299,
      type: 'camera',
      resolution: '3840x2160',
      frameRate: 30,
      fov: 120,
      protocols: ['USB 3.0', 'ROS 2', 'Ethernet']
    },
    {
      model: 'Velodyne VLP-16',
      tier: 'premium',
      price: 3999,
      type: 'lidar',
      range: 100,
      accuracy: '±3cm',
      protocols: ['Ethernet', 'ROS 2', 'CAN bus']
    },
    {
      model: 'Xsens MTi-670G',
      tier: 'premium',
      price: 1999,
      type: 'imu',
      accuracy: '±0.1°',
      protocols: ['RS232', 'USB', 'CAN bus', 'ROS 2']
    }
  ];

  const benchmarks: PerformanceBenchmark[] = [
    {
      category: 'simulation',
      metric: 'Isaac Sim Physics Rate',
      edgeValue: 30,
      midValue: 120,
      premiumValue: 240,
      unit: 'Hz'
    },
    {
      category: 'inference',
      metric: 'YOLOv8 Inference (640x640)',
      edgeValue: 15,
      midValue: 120,
      premiumValue: 300,
      unit: 'fps'
    },
    {
      category: 'inference',
      metric: 'BERT Large (batch=32)',
      edgeValue: 8,
      midValue: 85,
      premiumValue: 220,
      unit: 'tokens/s'
    },
    {
      category: 'rendering',
      metric: 'Unreal Engine 5 (1080p)',
      edgeValue: 15,
      midValue: 144,
      premiumValue: 240,
      unit: 'fps'
    },
    {
      category: 'training',
      metric: 'ResNet-50 Training',
      edgeValue: 8,
      midValue: 450,
      premiumValue: 1200,
      unit: 'images/s'
    }
  ];

  // State management
  const [filters, setFilters] = useState<FilterOptions>({
    tier: 'all',
    category: 'all',
    maxPrice: 2000,
    minPerformance: 0
  });

  const [sortField, setSortField] = useState<SortField>('price');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [selectedCategory, setSelectedCategory] = useState<'gpu' | 'cpu' | 'ram' | 'storage' | 'sensors'>('gpu');

  // Get data based on selected category
  const getCurrentData = useCallback(() => {
    switch (selectedCategory) {
      case 'gpu':
        return gpuData;
      case 'cpu':
        return cpuData;
      case 'ram':
        return ramData;
      case 'storage':
        return storageData;
      case 'sensors':
        return sensorData;
      default:
        return gpuData;
    }
  }, [selectedCategory]);

  // Filter and sort data
  const filteredAndSortedData = useMemo(() => {
    let data = getCurrentData();

    // Apply filters
    data = data.filter(item => {
      if (filters.tier !== 'all' && item.tier !== filters.tier) return false;
      if ('price' in item && item.price > filters.maxPrice) return false;
      return true;
    });

    // Sort data
    data = [...data].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case 'price':
          aValue = a.price;
          bValue = b.price;
          break;
        case 'name':
          aValue = a.model;
          bValue = b.model;
          break;
        case 'tier':
          const tierOrder = { edge: 0, mid: 1, premium: 2 };
          aValue = tierOrder[a.tier];
          bValue = tierOrder[b.tier];
          break;
        case 'performance':
          // Calculate performance score based on category
          if ('tensorTOPS' in a) {
            aValue = (a as GPUSpec).tensorTOPS;
            bValue = (b as GPUSpec).tensorTOPS;
          } else if ('cores' in a && 'threads' in a) {
            aValue = (a as CPUSpec).cores + (a as CPUSpec).threads * 0.5;
            bValue = (b as CPUSpec).cores + (b as CPUSpec).threads * 0.5;
          } else if ('speed' in a) {
            aValue = (a as RAMSpec).speed * ((a as RAMSpec).capacity / 16);
            bValue = (b as RAMSpec).speed * ((b as RAMSpec).capacity / 16);
          } else if ('readSpeed' in a) {
            aValue = (a as StorageSpec).readSpeed;
            bValue = (b as StorageSpec).readSpeed;
          } else {
            aValue = 0;
            bValue = 0;
          }
          break;
        default:
          aValue = a.price;
          bValue = b.price;
      }

      if (typeof aValue === 'string') {
        return sortOrder === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    });

    return data;
  }, [filters, sortField, sortOrder, getCurrentData]);

  // Calculate price-to-performance ratio
  const getPriceToPerformanceRatio = useCallback((item: any) => {
    let performance = 0;

    if ('tensorTOPS' in item) {
      performance = item.tensorTOPS;
    } else if ('cores' in item) {
      performance = item.cores + item.threads * 0.5;
    } else if ('speed' in item) {
      performance = item.speed * (item.capacity / 16);
    } else if ('readSpeed' in item) {
      performance = item.readSpeed;
    }

    return performance / item.price;
  }, []);

  // Export functionality
  const exportToCSV = useCallback(() => {
    const headers = ['Model', 'Tier', 'Price', 'Key Specs'];
    const rows = filteredAndSortedData.map(item => {
      const specs = [];
      if ('tensorTOPS' in item) {
        specs.push(`${(item as GPUSpec).tensorTOPS} TOPS`);
        specs.push(`${(item as GPUSpec).memory}GB ${(item as GPUSpec).memoryType}`);
      } else if ('cores' in item) {
        specs.push(`${(item as CPUSpec).cores}C/${(item as CPUSpec).threads}T`);
        specs.push(`${(item as CPUSpec).baseClock}-${(item as CPUSpec).boostClock}GHz`);
      }
      return [
        item.model,
        item.tier,
        `$${item.price}`,
        specs.join(' | ')
      ];
    });

    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hardware-comparison-${selectedCategory}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filteredAndSortedData, selectedCategory]);

  const exportToJSON = useCallback(() => {
    const jsonContent = JSON.stringify(filteredAndSortedData, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hardware-comparison-${selectedCategory}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filteredAndSortedData, selectedCategory]);

  // Handle component selection for BudgetCalculator integration
  const handleComponentSelect = (component: any) => {
    if (onComponentSelect) {
      onComponentSelect(component, selectedCategory);
    }
  };

  // Helper function to get performance bar color
  const getPerformanceColor = (ratio: number, maxRatio: number) => {
    const percentage = (ratio / maxRatio) * 100;
    if (percentage > 80) return 'bg-green-500';
    if (percentage > 60) return 'bg-blue-500';
    if (percentage > 40) return 'bg-yellow-500';
    return 'bg-gray-400';
  };

  // Calculate max ratio for performance bars
  const maxPerformanceRatio = useMemo(() => {
    return Math.max(...filteredAndSortedData.map(item => getPriceToPerformanceRatio(item)));
  }, [filteredAndSortedData, getPriceToPerformanceRatio]);

  return (
    <div className="w-full max-w-7xl mx-auto p-6 bg-white dark:bg-gray-900 rounded-lg shadow-lg">
      <h2 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">
        Hardware Comparison Tool
      </h2>

      {/* Category Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Component Category
        </label>
        <div className="grid grid-cols-5 gap-2">
          {[
            { id: 'gpu', label: 'GPU' },
            { id: 'cpu', label: 'CPU' },
            { id: 'ram', label: 'RAM' },
            { id: 'storage', label: 'Storage' },
            { id: 'sensors', label: 'Sensors' }
          ].map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id as any)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedCategory === cat.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Tier Filter
          </label>
          <select
            value={filters.tier}
            onChange={e => setFilters({ ...filters, tier: e.target.value as any })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
          >
            <option value="all">All Tiers</option>
            <option value="edge">Edge Kit</option>
            <option value="mid">Proxy Robot</option>
            <option value="premium">Premium Lab</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Max Price: ${filters.maxPrice}
          </label>
          <input
            type="range"
            min="0"
            max="2000"
            step="50"
            value={filters.maxPrice}
            onChange={e => setFilters({ ...filters, maxPrice: Number(e.target.value) })}
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Sort By
          </label>
          <select
            value={`${sortField}-${sortOrder}`}
            onChange={e => {
              const [field, order] = e.target.value.split('-');
              setSortField(field as SortField);
              setSortOrder(order as SortOrder);
            }}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
          >
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
            <option value="performance-desc">Performance: High to Low</option>
            <option value="performance-asc">Performance: Low to High</option>
            <option value="name-asc">Name: A to Z</option>
            <option value="tier-asc">Tier: Entry to Premium</option>
          </select>
        </div>
      </div>

      {/* Export Buttons */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={exportToCSV}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          Export to CSV
        </button>
        <button
          onClick={exportToJSON}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          Export to JSON
        </button>
        {onComponentSelect && (
          <div className="ml-auto text-sm text-gray-600 dark:text-gray-400 py-2">
            Click "Add to Budget" to include components in your configuration
          </div>
        )}
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-100 dark:bg-gray-800">
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white border-b">
                Model
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white border-b">
                Tier
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white border-b">
                Price
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white border-b">
                Specifications
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white border-b">
                Price/Performance
              </th>
              {onComponentSelect && (
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white border-b">
                  Action
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedData.map((item, index) => {
              const ratio = getPriceToPerformanceRatio(item);
              const isSelected = selectedComponents[selectedCategory]?.model === item.model;
              return (
                <tr key={index} className={`hover:bg-gray-50 dark:hover:bg-gray-800 border-b ${isSelected ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                    {item.model}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      item.tier === 'edge'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : item.tier === 'mid'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        : 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                    }`}>
                      {item.tier === 'edge' ? 'Edge Kit' : item.tier === 'mid' ? 'Proxy Robot' : 'Premium Lab'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-900 dark:text-white font-semibold">
                    ${item.price}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {selectedCategory === 'gpu' && (
                      <div>
                        <div>CUDA: {(item as GPUSpec).cudaCores} cores</div>
                        <div>Memory: {(item as GPUSpec).memory}GB {(item as GPUSpec).memoryType}</div>
                        <div>Tensor: {(item as GPUSpec).tensorTOPS} TOPS</div>
                        <div>Power: {(item as GPUSpec).powerConsumption}W</div>
                      </div>
                    )}
                    {selectedCategory === 'cpu' && (
                      <div>
                        <div>Cores/Threads: {(item as CPUSpec).cores}/{(item as CPUSpec).threads}</div>
                        <div>Clock: {(item as CPUSpec).baseClock}-{(item as CPUSpec).boostClock}GHz</div>
                        <div>Architecture: {(item as CPUSpec).architecture}</div>
                        <div>TDP: {(item as CPUSpec).tdp}W</div>
                      </div>
                    )}
                    {selectedCategory === 'ram' && (
                      <div>
                        <div>Capacity: {(item as RAMSpec).capacity}GB</div>
                        <div>Speed: {(item as RAMSpec).speed}MT/s</div>
                        <div>Type: {(item as RAMSpec).type}</div>
                        <div>Latency: CL{(item as RAMSpec).latency}</div>
                      </div>
                    )}
                    {selectedCategory === 'storage' && (
                      <div>
                        <div>Capacity: {(item as StorageSpec).capacity}GB</div>
                        <div>Type: {(item as StorageSpec).type} {(item as StorageSpec).interface}</div>
                        <div>Read/Write: {(item as StorageSpec).readSpeed}/{(item as StorageSpec).writeSpeed} MB/s</div>
                        <div>Endurance: {(item as StorageSpec).endurance}TBW</div>
                      </div>
                    )}
                    {selectedCategory === 'sensors' && (
                      <div>
                        <div>Type: {(item as SensorSpec).type}</div>
                        {(item as SensorSpec).resolution && <div>Resolution: {(item as SensorSpec).resolution}</div>}
                        {(item as SensorSpec).range && <div>Range: {(item as SensorSpec).range}m</div>}
                        {(item as SensorSpec).accuracy && <div>Accuracy: {(item as SensorSpec).accuracy}</div>}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getPerformanceColor(ratio, maxPerformanceRatio)}`}
                          style={{ width: `${(ratio / maxPerformanceRatio) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[80px]">
                        {ratio.toFixed(2)}
                      </span>
                    </div>
                  </td>
                  {onComponentSelect && (
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleComponentSelect(item)}
                        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                          isSelected
                            ? 'bg-green-600 text-white'
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                        }`}
                      >
                        {isSelected ? 'Selected' : 'Add to Budget'}
                      </button>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Performance Benchmarks */}
      <div className="mt-8">
        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
          Performance Benchmarks by Tier
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {benchmarks.map((benchmark, index) => (
            <div key={index} className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                {benchmark.metric}
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {benchmark.category} • {benchmark.unit}
              </p>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-green-600 dark:text-green-400">Edge</span>
                  <span className="text-gray-900 dark:text-white">
                    {benchmark.edgeValue} {benchmark.unit}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">Mid</span>
                  <span className="text-gray-900 dark:text-white">
                    {benchmark.midValue} {benchmark.unit}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-purple-600 dark:text-purple-400">Premium</span>
                  <span className="text-gray-900 dark:text-white">
                    {benchmark.premiumValue} {benchmark.unit}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Integration Note */}
      <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          <strong>Budget Integration:</strong> Selected components can be added to your custom configuration for detailed cost analysis in the Budget Calculator.
          The calculator will estimate total costs, cloud alternatives, and ROI projections.
        </p>
      </div>
    </div>
  );
};

export default HardwareComparison;