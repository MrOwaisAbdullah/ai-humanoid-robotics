import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import HardwareComparison from './HardwareComparison';

// Mock the global URL.createObjectURL for export functionality
global.URL.createObjectURL = jest.fn(() => 'mock-url');
global.URL.revokeObjectURL = jest.fn();
global.Blob = jest.fn((content, options) => ({ content, options })) as any;

describe('HardwareComparison', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  test('renders component with default category (GPU)', () => {
    render(<HardwareComparison />);

    expect(screen.getByText('Hardware Comparison Tool')).toBeInTheDocument();
    expect(screen.getByText('Component Category')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'GPU' })).toHaveClass('bg-[#10a37f]');
  });

  test('category selection changes active button', () => {
    render(<HardwareComparison />);

    const cpuButton = screen.getByRole('button', { name: 'CPU' });
    fireEvent.click(cpuButton);

    expect(cpuButton).toHaveClass('bg-[#10a37f]');
    expect(screen.getByRole('button', { name: 'GPU' })).not.toHaveClass('bg-[#10a37f]');
  });

  test('tier filter updates results', () => {
    render(<HardwareComparison />);

    const tierFilter = screen.getByDisplayValue('All Tiers');
    fireEvent.change(tierFilter, { target: { value: 'edge' } });

    expect(tierFilter).toHaveValue('edge');
  });

  test('price filter updates slider value', () => {
    render(<HardwareComparison />);

    const priceSlider = screen.getByRole('slider');
    expect(priceSlider).toHaveValue('2000');

    fireEvent.change(priceSlider, { target: { value: '1000' } });
    expect(priceSlider).toHaveValue('1000');
  });

  test('sort dropdown changes order', () => {
    render(<HardwareComparison />);

    const sortDropdown = screen.getByDisplayValue('Price: Low to High');
    fireEvent.change(sortDropdown, { target: { value: 'price-desc' } });

    expect(sortDropdown).toHaveValue('price-desc');
  });

  test('export buttons are present', () => {
    render(<HardwareComparison />);

    expect(screen.getByRole('button', { name: 'Export to CSV' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Export to JSON' })).toBeInTheDocument();
  });

  test('performance benchmarks are displayed', () => {
    render(<HardwareComparison />);

    expect(screen.getByText('Performance Benchmarks by Tier')).toBeInTheDocument();
    expect(screen.getByText('Isaac Sim Physics Rate')).toBeInTheDocument();
    expect(screen.getByText('YOLOv8 Inference (640x640)')).toBeInTheDocument();
  });

  test('GPU specifications are displayed correctly', () => {
    render(<HardwareComparison />);

    // GPU should be the default category
    expect(screen.getByText('CUDA: 1024 cores')).toBeInTheDocument(); // Jetson Orin Nano
    expect(screen.getByText('CUDA: 4352 cores')).toBeInTheDocument(); // RTX 4060 Ti
  });

  test('CPU category shows correct specifications', () => {
    render(<HardwareComparison />);

    const cpuButton = screen.getByRole('button', { name: 'CPU' });
    fireEvent.click(cpuButton);

    expect(screen.getByText('Cores/Threads: 6/12')).toBeInTheDocument(); // Intel i5-13400
    expect(screen.getByText('Cores/Threads: 24/48')).toBeInTheDocument(); // Threadripper
  });

  test('RAM category shows correct specifications', () => {
    render(<HardwareComparison />);

    const ramButton = screen.getByRole('button', { name: 'RAM' });
    fireEvent.click(ramButton);

    expect(screen.getByText('Capacity: 16GB')).toBeInTheDocument(); // Corsair Vengeance
    expect(screen.getByText('Capacity: 128GB')).toBeInTheDocument(); // G.Skill Trident
  });

  test('Storage category shows correct specifications', () => {
    render(<HardwareComparison />);

    const storageButton = screen.getByRole('button', { name: 'Storage' });
    fireEvent.click(storageButton);

    expect(screen.getByText('Type: NVMe PCIe 3.0')).toBeInTheDocument();
    expect(screen.getByText('Type: SATA SATA III')).toBeInTheDocument();
  });

  test('Sensors category shows correct specifications', () => {
    render(<HardwareComparison />);

    const sensorsButton = screen.getByRole('button', { name: 'Sensors' });
    fireEvent.click(sensorsButton);

    expect(screen.getByText('Type: camera')).toBeInTheDocument();
    expect(screen.getByText('Type: lidar')).toBeInTheDocument();
    expect(screen.getByText('Type: imu')).toBeInTheDocument();
  });
});