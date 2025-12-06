import React, { useState } from 'react';
import HardwareComparison from './HardwareComparison';
import { HardwareComponent } from '../BudgetCalculator';

interface HardwareComparisonContainerProps {
  onComponentsUpdate?: (components: Record<string, HardwareComponent>) => void;
}

const HardwareComparisonContainer: React.FC<HardwareComparisonContainerProps> = ({
  onComponentsUpdate
}) => {
  const [selectedComponents, setSelectedComponents] = useState<Record<string, any>>({});

  const handleComponentSelect = (component: any, category: string) => {
    const newSelection = {
      ...selectedComponents,
      [category]: component
    };
    setSelectedComponents(newSelection);

    // Convert to BudgetCalculator format if callback provided
    if (onComponentsUpdate) {
      const budgetComponents: Record<string, HardwareComponent> = {};

      // Convert GPU
      if (newSelection.gpu) {
        budgetComponents.gpu = {
          id: newSelection.gpu.model.toLowerCase().replace(/\s+/g, '-'),
          name: newSelection.gpu.model,
          category: 'compute' as const,
          basePrice: newSelection.gpu.price,
          description: `${newSelection.gpu.tier === 'edge' ? 'Entry-level' : newSelection.gpu.tier === 'mid' ? 'Mid-range' : 'High-end'} GPU`,
          specifications: {
            'CUDA Cores': newSelection.gpu.cudaCores?.toString() || 'N/A',
            'Memory': `${newSelection.gpu.memory}GB ${newSelection.gpu.memoryType || 'N/A'}`,
            'Performance': `${newSelection.gpu.tensorTOPS || 'N/A'} TOPS`,
            'Power': `${newSelection.gpu.powerConsumption || 'N/A'}W`
          }
        };
      }

      // Convert CPU
      if (newSelection.cpu) {
        budgetComponents.cpu = {
          id: newSelection.cpu.model.toLowerCase().replace(/\s+/g, '-'),
          name: newSelection.cpu.model,
          category: 'compute' as const,
          basePrice: newSelection.cpu.price,
          description: `${newSelection.cpu.tier === 'edge' ? 'Entry-level' : newSelection.cpu.tier === 'mid' ? 'Mid-range' : 'High-end'} CPU`,
          specifications: {
            'Cores/Threads': `${newSelection.cpu.cores}/${newSelection.cpu.threads}`,
            'Clock Speed': `${newSelection.cpu.baseClock}-${newSelection.cpu.boostClock}GHz`,
            'Architecture': newSelection.cpu.architecture,
            'TDP': `${newSelection.cpu.tdp}W`
          }
        };
      }

      // Convert RAM
      if (newSelection.ram) {
        budgetComponents.ram = {
          id: newSelection.ram.model.toLowerCase().replace(/\s+/g, '-'),
          name: newSelection.ram.model,
          category: 'storage' as const,
          basePrice: newSelection.ram.price,
          description: `${newSelection.ram.capacity}GB ${newSelection.ram.type} RAM Kit`,
          specifications: {
            'Capacity': `${newSelection.ram.capacity}GB`,
            'Speed': `${newSelection.ram.speed}MT/s`,
            'Type': newSelection.ram.type,
            'Modules': `${newSelection.ram.modules}x${newSelection.ram.capacity / newSelection.ram.modules}GB`
          }
        };
      }

      // Convert Storage
      if (newSelection.storage) {
        budgetComponents.storage = {
          id: newSelection.storage.model.toLowerCase().replace(/\s+/g, '-'),
          name: newSelection.storage.model,
          category: 'storage' as const,
          basePrice: newSelection.storage.price,
          description: `${newSelection.storage.capacity}GB ${newSelection.storage.type} ${newSelection.storage.interface}`,
          specifications: {
            'Capacity': `${newSelection.storage.capacity}GB`,
            'Type': `${newSelection.storage.type} ${newSelection.storage.interface}`,
            'Read Speed': `${newSelection.storage.readSpeed}MB/s`,
            'Write Speed': `${newSelection.storage.writeSpeed}MB/s`
          }
        };
      }

      // Convert Sensor
      if (newSelection.sensors) {
        budgetComponents.sensors = {
          id: newSelection.sensors.model.toLowerCase().replace(/\s+/g, '-'),
          name: newSelection.sensors.model,
          category: 'sensors' as const,
          basePrice: newSelection.sensors.price,
          description: `${newSelection.sensors.tier === 'edge' ? 'Entry-level' : newSelection.sensors.tier === 'mid' ? 'Mid-range' : 'Professional'} ${newSelection.sensors.type} sensor`,
          specifications: {
            'Type': newSelection.sensors.type,
            'Resolution': newSelection.sensors.resolution || 'N/A',
            'Range': newSelection.sensors.range ? `${newSelection.sensors.range}m` : 'N/A',
            'Accuracy': newSelection.sensors.accuracy || 'N/A'
          }
        };
      }

      onComponentsUpdate(budgetComponents);
    }
  };

  return (
    <HardwareComparison
      onComponentSelect={handleComponentSelect}
      selectedComponents={selectedComponents}
    />
  );
};

export default HardwareComparisonContainer;