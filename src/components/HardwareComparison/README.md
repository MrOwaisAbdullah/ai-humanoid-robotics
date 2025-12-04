# Hardware Comparison Component

A comprehensive hardware comparison tool for the Physical AI & Humanoid Robotics course that helps students make informed hardware decisions based on budget and performance requirements.

## Features

- **Multi-Category Comparison**: Compare GPUs, CPUs, RAM, Storage, and Sensors
- **Tier-Based Organization**:
  - Edge Kit (~$700): Entry-level components
  - Proxy Robot ($1,800-$3,000): Mid-range components
  - Premium Lab ($16,000+): High-end components
- **Interactive Filtering**: Filter by tier, price, and performance metrics
- **Advanced Sorting**: Sort by price, performance, name, or tier
- **Price-to-Performance Analysis**: Visual indicators showing value for money
- **Export Functionality**: Export comparison data to CSV or JSON
- **Budget Calculator Integration**: Seamless integration with the existing BudgetCalculator component
- **Performance Benchmarks**: Real-world performance metrics for robotics workloads
- **Responsive Design**: Mobile-friendly with Tailwind CSS
- **Dark Mode Support**: Built-in dark theme compatibility

## Component Structure

```
HardwareComparison/
├── index.tsx                    # Main exports
├── HardwareComparison.tsx       # Standalone comparison component
├── HardwareComparisonContainer.tsx  # Integration wrapper for BudgetCalculator
├── Demo.tsx                     # Example usage and demo
└── README.md                    # This file
```

## Usage

### Standalone Component

```tsx
import HardwareComparison from '@/components/HardwareComparison';

function MyComponent() {
  return <HardwareComparison />;
}
```

### Integrated with BudgetCalculator

```tsx
import { HardwareComparisonContainer } from '@/components/HardwareComparison';

function MyComponent() {
  const handleComponentsUpdate = (components) => {
    // Handle selected components
    console.log('Selected:', components);
  };

  return (
    <HardwareComparisonContainer
      onComponentsUpdate={handleComponentsUpdate}
    />
  );
}
```

## Hardware Categories

### GPUs
- **NVIDIA RTX Series**: 4060, 4070 Ti, 4090, 5090
- **Jetson Series**: Orin Nano for edge AI

### CPUs
- **Intel Core**: i5, i7, i9 series
- **AMD Ryzen**: 7, 9 series
- **Threadripper PRO**: For workstation-grade performance

### RAM
- DDR4 vs DDR5 comparisons
- Capacity options: 16GB to 128GB
- Speed ratings up to 6800MT/s

### Storage
- NVMe SSD vs SATA comparisons
- Performance tiers with read/write speeds
- Endurance ratings (TBW)

### Sensors
- **Cameras**: Intel RealSense D435i, OAK-D Lite
- **LiDAR**: Velodyne VLP-16
- **IMU**: Xsens MTi-670G

## Performance Benchmarks

The component includes real-world benchmarks for robotics workloads:
- Isaac Sim Physics Rate
- YOLOv8 Inference speeds
- BERT Large processing
- Unreal Engine 5 rendering
- ResNet-50 training throughput

## Customization

### Adding New Hardware

To add new hardware components, update the data arrays in `HardwareComparison.tsx`:

```tsx
const gpuData: GPUSpec[] = [
  // ... existing data
  {
    model: 'New GPU Model',
    tier: 'mid',
    price: 599,
    // ... other specifications
  }
];
```

### Modifying Filters

Adjust filter options by modifying the `FilterOptions` interface and default state.

### Custom Styling

The component uses Tailwind CSS classes. Modify classes directly in the JSX to customize the appearance.

## Integration Notes

The component integrates with the BudgetCalculator through the `HardwareComparisonContainer` wrapper. When components are selected:

1. They are converted to the BudgetCalculator's expected format
2. Specifications are mapped appropriately
3. Prices are maintained across both components
4. The callback provides all selected components for budget calculations

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Dependencies

- React 19+
- TypeScript 5+
- Tailwind CSS 4+

No additional dependencies required - built with standard web APIs.