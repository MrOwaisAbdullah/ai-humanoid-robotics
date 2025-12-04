# Ubuntu 22.04 Robotics Development Setup Scripts

This directory contains automated installation scripts for setting up a complete robotics development environment on Ubuntu 22.04 LTS.

## Files Overview

### `install-ubuntu-robotics.sh`
Main installation script that configures a complete robotics development environment including:
- Essential development tools (git, vim, build-essential, etc.)
- NVIDIA drivers and CUDA toolkit 12.2
- ROS 2 Humble with development tools
- Python 3.10 virtual environment with ML libraries
- ROS 2 workspace with essential packages
- Gazebo simulation environment
- Isaac Sim prerequisites
- Performance optimizations
- Desktop shortcuts
- Validation scripts

## Quick Start

### Prerequisites
- Ubuntu 22.04 LTS (clean installation recommended)
- At least 8GB RAM (16GB+ recommended)
- At least 20GB free disk space
- Internet connection
- NVIDIA GPU (optional but recommended for AI workloads)
- sudo privileges on the account

### Installation

1. **Download the script**
   ```bash
   wget https://your-domain.com/hardware-guides/ubuntu-setup/install-ubuntu-robotics.sh
   ```

2. **Make it executable**
   ```bash
   chmod +x install-ubuntu-robotics.sh
   ```

3. **Run the installation**
   ```bash
   ./install-ubuntu-robotics.sh
   ```

4. **Reboot after installation** (required for NVIDIA drivers)

## What Gets Installed

### Development Tools
- **Build Tools**: GCC, CMake, Make, pkg-config
- **Version Control**: Git
- **Editors**: Vim
- **Monitoring**: htop, tree, net-tools
- **SSH**: OpenSSH server for remote access

### Graphics and AI
- **NVIDIA Drivers**: Latest stable version with CUDA 12.2
- **GPU Computing**: CUDA toolkit, cuDNN
- **Python ML**: PyTorch, TensorFlow, OpenCV, NumPy, SciPy

### Robotics Framework
- **ROS 2 Humble**: Latest long-term support version
- **Gazebo**: Version 11 with physics simulation
- **Development Tools**: rosdep, colcon, vcstool

### Python Environment
- **Virtual Environment**: Isolated Python 3.10 environment
- **Scientific Computing**: NumPy, SciPy, Matplotlib
- **Machine Learning**: PyTorch, TensorFlow, Scikit-learn
- **Development**: Jupyter Notebook, IPython

### Additional Tools
- **Docker**: Containerization support
- **Performance Scripts**: Automatic performance optimization
- **Desktop Shortcuts**: Quick access to ROS 2 and Gazebo

## Post-Installation

### Validation
Run the validation script to check your installation:
```bash
~/validate-robotics-setup.sh
```

### Performance Configuration
Optimize your system for robotics workloads:
```bash
~/set-performance-mode.sh
```

### Environment Setup
Open a new terminal (or use the ROS2 Terminal desktop shortcut) and verify:
```bash
# Check ROS 2
ros2 doctor

# Test basic functionality
ros2 run demo_nodes_cpp talker &
ros2 run demo_nodes_py listener
```

## Directory Structure Created

```
~/ros2_ws/                    # ROS 2 workspace
├── src/                      # Source packages
├── build/                    # Build artifacts
├── install/                  # Built packages
├── log/                      # Build logs
└── env/                      # Python virtual environment

~/set-performance-mode.sh     # Performance configuration script
~/validate-robotics-setup.sh  # Installation validation script
~/Desktop/
├── ROS2_Terminal.desktop     # ROS 2 terminal shortcut
└── Gazebo.desktop           # Gazebo simulator shortcut
```

## Troubleshooting

### Common Issues

**NVIDIA Driver Issues**
```bash
# Reinstall drivers
sudo apt purge nvidia-*
sudo ubuntu-drivers autoinstall
sudo reboot
```

**ROS 2 Environment Not Found**
```bash
# Source environment manually
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
```

**Python Package Issues**
```bash
# Reinstall Python packages
~/ros2_ws/env/bin/pip install --upgrade package_name
```

**Permission Issues with Docker**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
```

### Getting Help

- **ROS 2 Documentation**: https://docs.ros.org/en/humble/
- **CUDA Documentation**: https://docs.nvidia.com/cuda/
- **Gazebo Documentation**: http://gazebosim.org/tutorials
- **Course Forums**: Available through the learning platform

## System Requirements

### Minimum Requirements
- **OS**: Ubuntu 22.04 LTS
- **CPU**: Intel i5/AMD Ryzen 5 (8 threads recommended)
- **RAM**: 8GB (16GB+ recommended)
- **Storage**: 20GB free space
- **GPU**: Integrated graphics (NVIDIA GPU recommended for AI)

### Recommended Requirements
- **CPU**: Intel i7/AMD Ryzen 7 (12+ cores)
- **RAM**: 32GB+ DDR4
- **Storage**: 50GB+ SSD
- **GPU**: NVIDIA RTX 4070+ (12GB+ VRAM)
- **Network**: 100Mbps+ internet

## Customization Options

### Selective Installation
If you want to install only specific components, you can modify the `install-ubuntu-robotics.sh` script and comment out the functions you don't need.

### Custom Python Packages
Add additional Python packages to the `install_python_env()` function:
```bash
~/ros2_ws/env/bin/pip install your-custom-package
```

### Additional ROS 2 Packages
Clone additional ROS 2 packages in the workspace:
```bash
cd ~/ros2_ws/src
git clone https://github.com/your-org/your-package.git
cd ~/ros2_ws
colcon build --packages-select your-package
```

## Performance Tips

### GPU Optimization
- Use the performance script after installation
- Monitor GPU temperature during intensive workloads
- Consider undervolting for better thermals

### System Optimization
- Use SSD for system disk
- Configure swap space appropriately
- Disable unnecessary services
- Use the performance mode script provided

## Security Considerations

### Best Practices
- Keep system updated regularly
- Use firewall (ufw) for network security
- Regular backup of important data
- Use strong passwords and SSH keys

### Docker Security
- Run containers with minimal privileges
- Use official images when possible
- Regularly update Docker and containers

## Integration with Course Materials

### Lab Exercises
- All lab exercises are designed to work with this environment
- ROS 2 workspaces will be compatible with course materials
- Python notebooks will run in the configured environment

### Cloud Integration
- Scripts can be adapted for cloud VM deployment
- AWS configuration scripts are available in the cloud-setup directory

## Support and Updates

### Version History
- **v1.0** (2025-12-04): Initial release with complete robotics stack

### Updates
Check for script updates regularly:
```bash
wget https://your-domain.com/hardware-guides/ubuntu-setup/install-ubuntu-robotics.sh
```

### Contributing
Found issues or improvements? Please report them through the course issue tracker or forums.

---

**Note**: This script is designed for educational purposes and development environments. For production deployments, additional security and configuration considerations may be necessary.