#!/bin/bash
# Ubuntu 22.04 LTS Robotics Development Environment Setup Script
# Physical AI & Humanoid Robotics Textbook
# Version: 1.0
# Date: 2025-12-04

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Run as regular user with sudo privileges."
   exit 1
fi

# System requirements check
check_system_requirements() {
    print_status "Checking system requirements..."

    # Check Ubuntu version
    if [[ $(lsb_release -rs) != "22.04" ]]; then
        print_error "This script requires Ubuntu 22.04 LTS"
        exit 1
    fi

    # Check if we have internet connection
    if ! ping -c 1 google.com &> /dev/null; then
        print_error "No internet connection. Please check your network."
        exit 1
    fi

    # Check available disk space (need at least 20GB)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 20971520 ]]; then  # 20GB in KB
        print_error "Insufficient disk space. Need at least 20GB free."
        exit 1
    fi

    # Check RAM (need at least 8GB)
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $total_ram -lt 8 ]]; then
        print_warning "System has less than 8GB RAM. Performance may be limited."
    fi

    print_success "System requirements check passed"
}

# Update system packages
update_system() {
    print_status "Updating system packages..."

    sudo apt update
    sudo apt upgrade -y
    sudo apt autoremove -y
    sudo apt autoclean

    print_success "System updated successfully"
}

# Install essential packages
install_essentials() {
    print_status "Installing essential packages..."

    sudo apt install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        tree \
        build-essential \
        cmake \
        pkg-config \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        unzip \
        p7zip-full \
        net-tools \
        openssh-server \
        gnome-terminal

    print_success "Essential packages installed"
}

# Install NVIDIA drivers
install_nvidia_drivers() {
    print_status "Installing NVIDIA drivers..."

    # Check if NVIDIA GPU is present
    if ! lspci | grep -i nvidia > /dev/null; then
        print_warning "No NVIDIA GPU detected. Skipping driver installation."
        return
    fi

    # Add NVIDIA repository
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
    sudo dpkg -i cuda-keyring_1.1-1_all.deb
    sudo apt-get update

    # Install NVIDIA driver
    sudo apt-get install -y cuda-toolkit-12-2 nvidia-driver-535

    # Configure environment
    echo 'export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}' >> ~/.bashrc

    print_success "NVIDIA drivers installed. Please reboot after script completes."
}

# Install ROS 2 Humble
install_ros2() {
    print_status "Installing ROS 2 Humble..."

    # Set locale
    sudo apt update && sudo apt install -y locales
    sudo locale-gen en_US en_US.UTF-8
    sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
    export LANG=en_US.UTF-8

    # Add ROS 2 repository
    sudo apt install -y software-properties-common
    sudo add-apt-repository universe
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

    # Install ROS 2
    sudo apt update
    sudo apt install -y ros-humble-desktop python3-pip

    # Install development tools
    sudo apt install -y python3-rosdep python3-vcstool
    sudo rosdep init
    rosdep update

    # Setup environment
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

    print_success "ROS 2 Humble installed"
}

# Install Python development environment
install_python_env() {
    print_status "Setting up Python development environment..."

    # Install Python development packages
    sudo apt install -y \
        python3.10-venv \
        python3.10-dev \
        python3-pip \
        python3-wheel

    # Create virtual environment for robotics
    mkdir -p ~/ros2_ws/env
    python3.10 -m venv ~/ros2_ws/env
    echo "source ~/ros2_ws/env/bin/activate" >> ~/.bashrc

    # Install essential Python packages
    ~/ros2_ws/env/bin/pip install --upgrade pip setuptools wheel

    ~/ros2_ws/env/bin/pip install \
        numpy \
        scipy \
        matplotlib \
        opencv-python \
        pandas \
        scikit-learn \
        jupyter \
        notebook \
        ipykernel \
        wheel

    # Install PyTorch with CUDA support
    ~/ros2_ws/env/bin/pip install \
        torch \
        torchvision \
        torchaudio \
        --index-url https://download.pytorch.org/whl/cu118

    # Install TensorFlow
    ~/ros2_ws/env/bin/pip install tensorflow-gpu

    print_success "Python environment configured"
}

# Create ROS 2 workspace
create_workspace() {
    print_status "Creating ROS 2 workspace..."

    mkdir -p ~/ros2_ws/src
    cd ~/ros2_ws

    # Clone essential packages
    cd src
    git clone https://github.com/ros-perception/vision_opencv.git
    git clone https://github.com/ros-drivers/usb_cam.git
    git clone https://github.com/ros-geometry/geometry2.git

    # Build workspace
    cd ~/ros2_ws
    colcon build --symlink-install

    print_success "ROS 2 workspace created and built"
}

# Install Gazebo simulation
install_gazebo() {
    print_status "Installing Gazebo simulation..."

    # Install Gazebo
    sudo apt install -y \
        gazebo11 \
        libgazebo11-dev \
        ros-humble-gazebo-ros-pkgs

    # Install Gazebo plugins and models
    sudo apt install -y \
        gazebo11-plugin-base \
        gazebo11-robotics-plugins

    # Download Gazebo models
    mkdir -p ~/.gazebo/models
    cd ~/.gazebo/models
    wget https://raw.githubusercontent.com/osrf/gazebo_models/master/.gitignore -O .gitignore

    print_success "Gazebo installed"
}

# Install Isaac Sim prerequisites
install_isaac_prerequisites() {
    print_status "Installing Isaac Sim prerequisites..."

    # Install additional dependencies
    sudo apt install -y \
        libegl1-mesa-dev \
        libgl1-mesa-dev \
        libgles2-mesa-dev \
        libwayland-dev \
        libxkbcommon-dev \
        libxrandr-dev \
        libxcursor-dev \
        libxinerama-dev \
        libxi-dev

    # Install Docker for containerization
    sudo apt-get update
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg

    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Set up the repository
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Add user to docker group
    sudo usermod -aG docker $USER

    print_success "Isaac Sim prerequisites installed"
}

# Configure performance settings
configure_performance() {
    print_status "Configuring performance settings..."

    # Create performance script
    cat > ~/set-performance-mode.sh << 'EOF'
#!/bin/bash
# Performance mode configuration for robotics development

# Set CPU governor to performance
echo "Setting CPU governor to performance mode..."
sudo cpupower frequency-set -g performance

# Configure NVIDIA GPU for maximum performance
if command -v nvidia-smi &> /dev/null; then
    echo "Configuring NVIDIA GPU for maximum performance..."
    sudo nvidia-smi -pm 1
    sudo nvidia-smi -ac 877,1215
fi

# Configure system limits for real-time performance
echo "Configuring system limits..."
echo '* soft nofile 65536' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65536' | sudo tee -a /etc/security/limits.conf
echo '* soft nproc 32768' | sudo tee -a /etc/security/limits.conf
echo '* hard nproc 32768' | sudo tee -a /etc/security/limits.conf

echo "Performance mode configured. Please restart your session."
EOF

    chmod +x ~/set-performance-mode.sh

    # Configure memory management
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

    print_success "Performance settings configured"
}

# Create desktop shortcuts
create_shortcuts() {
    print_status "Creating desktop shortcuts..."

    # ROS 2 terminal shortcut
    cat > ~/Desktop/ROS2_Terminal.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=ROS2 Terminal
Comment=Terminal with ROS 2 environment
Exec=gnome-terminal -- bash -c "source /opt/ros/humble/setup.bash; source ~/ros2_ws/install/setup.bash; exec bash"
Icon=terminal
Terminal=false
Categories=Development;
EOF

    # Gazebo shortcut
    cat > ~/Desktop/Gazebo.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Gazebo Simulator
Comment=Gazebo Robot Simulation
Exec=gazebo
Icon=gazebo
Terminal=false
Categories=Science;Engineering;
EOF

    # Make shortcuts executable
    chmod +x ~/Desktop/*.desktop

    print_success "Desktop shortcuts created"
}

# Create validation script
create_validation_script() {
    print_status "Creating validation script..."

    cat > ~/validate-robotics-setup.sh << 'EOF'
#!/bin/bash
# Validate robotics development environment

echo "Robotics Environment Validation"
echo "=============================="

# Check ROS 2 installation
if [ -f /opt/ros/humble/setup.bash ]; then
    echo "✓ ROS 2 Humble installed"
else
    echo "✗ ROS 2 Humble not found"
fi

# Check NVIDIA drivers
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA drivers installed"
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits
else
    echo "✗ NVIDIA drivers not found"
fi

# Check CUDA installation
if command -v nvcc &> /dev/null; then
    echo "✓ CUDA installed"
    nvcc --version | head -1
else
    echo "✗ CUDA not found"
fi

# Check Python environment
if [ -d ~/ros2_ws/env ]; then
    echo "✓ Python environment created"
else
    echo "✗ Python environment not found"
fi

# Check ROS 2 workspace
if [ -f ~/ros2_ws/install/setup.bash ]; then
    echo "✓ ROS 2 workspace built"
else
    echo "✗ ROS 2 workspace not built"
fi

# Check Gazebo installation
if command -v gazebo &> /dev/null; then
    echo "✓ Gazebo installed"
    gazebo --version | head -1
else
    echo "✗ Gazebo not found"
fi

echo ""
echo "To run validation with ROS 2 testing:"
echo "source /opt/ros/humble/setup.bash"
echo "ros2 doctor"
EOF

    chmod +x ~/validate-robotics-setup.sh

    print_success "Validation script created"
}

# Main installation function
main() {
    echo "Ubuntu 22.04 Robotics Development Environment Setup"
    echo "==================================================="
    echo ""
    echo "This script will install and configure:"
    echo "- Essential development tools"
    echo "- NVIDIA drivers and CUDA"
    echo "- ROS 2 Humble"
    echo "- Python development environment"
    echo "- Gazebo simulation"
    echo "- Isaac Sim prerequisites"
    echo "- Performance optimizations"
    echo ""
    echo "This will require approximately 15GB of disk space and 30-60 minutes."
    echo ""

    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi

    # Run installation steps
    check_system_requirements
    update_system
    install_essentials
    install_nvidia_drivers
    install_ros2
    install_python_env
    create_workspace
    install_gazebo
    install_isaac_prerequisites
    configure_performance
    create_shortcuts
    create_validation_script

    echo ""
    echo "Installation completed successfully!"
    echo ""
    echo "IMPORTANT:"
    echo "1. Please reboot your system to complete NVIDIA driver installation"
    echo "2. Run ~/validate-robotics-setup.sh to validate the installation"
    echo "3. Run ~/set-performance-mode.sh to configure performance settings"
    echo "4. Use the desktop shortcuts for quick access to ROS 2 and Gazebo"
    echo ""
    echo "Getting started:"
    echo "1. Open a new terminal (or run the ROS2 Terminal desktop shortcut)"
    echo "2. Try: ros2 run demo_nodes_cpp talker"
    echo "3. In another terminal: ros2 run demo_nodes_py listener"
    echo ""
    print_success "Robotics development environment setup complete!"
}

# Run main function
main "$@"