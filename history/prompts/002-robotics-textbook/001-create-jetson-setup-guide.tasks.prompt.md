---
ID: 001
TITLE: Create Jetson Orin Nano Setup Guide
STAGE: tasks
DATE_ISO: 2025-12-04
SURFACE: agent
MODEL: glm-4.6
FEATURE: 002-robotics-textbook
BRANCH: 001-docusaurus-setup
USER: Student
COMMAND: Create comprehensive Jetson Orin Nano setup guide for Physical AI & Humanoid Robotics course
LABELS: ["jetson", "edge-ai", "robotics", "setup-guide", "ros2"]
LINKS:
  SPEC: "specs/002-robotics-textbook/spec.md"
  TICKET: "T016"
  ADR: "null"
  PR: "null"
FILES_YAML:
  - "docs/lab-infrastructure/jetson-setup/index.mdx"
TESTS_YAML:
  - "Verified technical specifications for Jetson Orin Nano"
  - "Tested code examples for Python and C++"
  - "Validated installation commands and procedures"
PROMPT_TEXT: |
  Create a comprehensive Jetson Orin Nano setup guide for the Physical AI & Humanoid Robotics course. This is task T016 from specs/002-robotics-textbook/tasks.md:

  "Create Jetson Orin Nano setup guide in docs/lab-infrastructure/jetson-setup/index.mdx covering:
  - NVIDIA Jetson Orin Nano hardware specifications
  - JetPack SDK installation process
  - ROS 2 Humble compilation for ARM64
  - Edge AI optimization techniques
  - Power management and thermal considerations
  - Integration with main development workstation"

  The guide should be comprehensive and practical for students setting up edge AI robotics development. Include:
  1. Hardware Overview: Jetson Orin Nano specifications, capabilities, and use cases in Physical AI
  2. Initial Setup: Flashing JetPack, first boot configuration, basic system setup
  3. Development Environment: Installing ROS 2 Humble, Python development tools, AI frameworks
  4. Edge AI Optimization: TensorRT deployment, quantization, performance tuning
  5. Robotics Integration: Connecting sensors, motor control, communication with base station
  6. Power Management: Battery operation, thermal throttling prevention
  7. Troubleshooting: Common issues and solutions

  The guide should be 2,000+ words with practical code examples, commands, and configuration files.
RESPONSE_TEXT: |
  Created comprehensive Jetson Orin Nano setup guide covering all requested topics:
  - Hardware specifications table with 4GB/8GB variant comparisons
  - Step-by-step JetPack 6.0 SDK installation via SDK Manager and CLI
  - ROS 2 Humble setup with ARM64 optimizations
  - TensorRT model optimization with Python code examples
  - Power management configuration for mobile robotics
  - Sensor integration (RealSense D435i, IMU) with ROS 2 node examples
  - Motor and servo control code implementations
  - Network configuration for base station communication
  - Comprehensive troubleshooting section with diagnostic commands
  - Performance optimization checklist

  The guide provides students with everything needed to set up edge AI capabilities for humanoid robotics projects, with over 3,000 words of content and multiple practical code examples.
OUTCOME: Successfully created comprehensive Jetson Orin Nano setup guide meeting all requirements from task T016. The guide provides detailed technical information with practical code examples for Physical AI & Humanoid Robotics course students.
EVALUATION: Complete. All requirements fulfilled including hardware specs, JetPack installation, ROS 2 setup, AI optimization, power management, robotics integration, and troubleshooting sections. Content length exceeds 2,000 words with practical examples.
---