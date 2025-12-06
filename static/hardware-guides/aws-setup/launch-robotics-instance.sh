#!/bin/bash
# AWS Robotics Instance Launcher
# Launches optimized g5.2xlarge instance for Physical AI development
# Physical AI & Humanoid Robotics Textbook
# Version: 1.0
# Date: 2025-12-04

set -e

# Configuration variables
INSTANCE_TYPE="g5.2xlarge"
AMI_ID="ami-0c02fb55956c7d316"  # Ubuntu 22.04 LTS
KEY_NAME="robotics-key"
SECURITY_GROUP_NAME="robotics-sg"
IAM_INSTANCE_PROFILE="RoboticsInstanceProfile"
REGION="us-east-1"
SPOT_PRICE="0.50"  # Spot instance price threshold
INSTANCE_NAME="robotics-dev-instance"
PROJECT_TAG="physical-ai-course"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check AWS CLI installation
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi

    # Check jq for JSON processing
    if ! command -v jq &> /dev/null; then
        print_warning "jq not found. Installing jq..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update && sudo apt-get install -y jq
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install jq
        else
            print_error "Please install jq manually."
            exit 1
        fi
    fi

    print_success "Prerequisites check passed"
}

# Create SSH key pair if it doesn't exist
create_ssh_key() {
    print_status "Checking SSH key pair..."

    if ! aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &> /dev/null; then
        print_status "Creating SSH key pair: $KEY_NAME"

        # Generate SSH key pair locally
        ssh-keygen -t rsa -b 4096 -f "$HOME/.ssh/$KEY_NAME" -N "" -C "robotics-key-$(date +%s)"
        chmod 600 "$HOME/.ssh/$KEY_NAME"

        # Import public key to AWS
        aws ec2 import-key-pair \
            --key-name "$KEY_NAME" \
            --public-key-material fileb://"$HOME/.ssh/$KEY_NAME.pub" \
            --region "$REGION"

        print_success "SSH key pair created and imported to AWS"
        print_status "Private key saved to: $HOME/.ssh/$KEY_NAME"
    else
        print_success "SSH key pair '$KEY_NAME' already exists"
    fi
}

# Create security group if it doesn't exist
create_security_group() {
    print_status "Checking security group..."

    # Get VPC ID
    VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --query 'Vpcs[0].VpcId' --output text)

    if ! aws ec2 describe-security-groups --group-names "$SECURITY_GROUP_NAME" --region "$REGION" &> /dev/null; then
        print_status "Creating security group: $SECURITY_GROUP_NAME"

        SG_ID=$(aws ec2 create-security-group \
            --group-name "$SECURITY_GROUP_NAME" \
            --description "Security group for robotics development" \
            --vpc-id "$VPC_ID" \
            --region "$REGION" \
            --query 'GroupId' \
            --output text)

        # Allow SSH access
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port 22 \
            --cidr 0.0.0.0/0 \
            --region "$REGION"

        # Allow Jupyter Notebook access
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port 8888 \
            --cidr 0.0.0.0/0 \
            --region "$REGION"

        # Allow HTTP/HTTPS
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port 80 \
            --cidr 0.0.0.0/0 \
            --region "$REGION"

        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port 443 \
            --cidr 0.0.0.0/0 \
            --region "$REGION"

        # Allow Gazebo ports
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port 11345 \
            --cidr 0.0.0.0/0 \
            --region "$REGION"

        print_success "Security group created: $SG_ID"
    else
        SG_ID=$(aws ec2 describe-security-groups \
            --group-names "$SECURITY_GROUP_NAME" \
            --region "$REGION" \
            --query 'SecurityGroups[0].GroupId' \
            --output text)
        print_success "Security group '$SECURITY_GROUP_NAME' already exists: $SG_ID"
    fi

    echo "$SG_ID" > /tmp/robotics_sg_id.txt
}

# Create IAM instance profile if it doesn't exist
create_iam_role() {
    print_status "Checking IAM instance profile..."

    # Create trust policy
    cat > /tmp/instance-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create IAM role for robotics instance
    if ! aws iam get-role --role-name "$IAM_INSTANCE_PROFILE" --region "$REGION" &> /dev/null; then
        print_status "Creating IAM role: $IAM_INSTANCE_PROFILE"

        ROLE_ARN=$(aws iam create-role \
            --role-name "$IAM_INSTANCE_PROFILE" \
            --assume-role-policy-document file:///tmp/instance-trust-policy.json \
            --query 'Role.Arn' \
            --output text)

        # Attach policies
        aws iam attach-role-policy \
            --role-name "$IAM_INSTANCE_PROFILE" \
            --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

        aws iam attach-role-policy \
            --role-name "$IAM_INSTANCE_PROFILE" \
            --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

        # Create instance profile
        aws iam create-instance-profile --instance-profile-name "$IAM_INSTANCE_PROFILE"
        aws iam add-role-to-instance-profile \
            --instance-profile-name "$IAM_INSTANCE_PROFILE" \
            --role-name "$IAM_INSTANCE_PROFILE"

        print_success "IAM role and instance profile created"
    else
        print_success "IAM role '$IAM_INSTANCE_PROFILE' already exists"
    fi

    # Wait for role to be ready
    sleep 10
}

# Create user data script
create_user_data() {
    cat > /tmp/robotics-user-data.sh << 'EOF'
#!/bin/bash
# User data script for robotics development instance

# Log setup progress
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting robotics instance setup..."

# Update system
apt-get update && apt-get upgrade -y

# Install NVIDIA drivers and CUDA
echo "Installing NVIDIA drivers..."
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
dpkg -i cuda-keyring_1.1-1_all.deb
apt-get update
apt-get install -y cuda-toolkit-12-2 nvidia-driver-535

# Configure CUDA environment
echo 'export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}' >> /etc/environment
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}' >> /etc/environment

# Install ROS 2 Humble
echo "Installing ROS 2 Humble..."
apt-get install -y software-properties-common
add-apt-repository universe
apt-get update && apt-get install -y curl

curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null

apt-get update
apt-get install -y ros-humble-desktop python3-pip python3-rosdep python3-vcstool

# Configure ROS 2
rosdep init
rosdep update
echo "source /opt/ros/humble/setup.bash" >> /home/ubuntu/.bashrc

# Install Python packages
echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install numpy scipy matplotlib opencv-python pandas scikit-learn jupyter notebook
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install tensorflow-gpu

# Install Gazebo
echo "Installing Gazebo..."
apt-get install -y gazebo11 libgazebo11-dev ros-humble-gazebo-ros-pkgs

# Create ROS 2 workspace
echo "Creating ROS 2 workspace..."
mkdir -p /home/ubuntu/ros2_ws/src
cd /home/ubuntu/ros2_ws/src
git clone https://github.com/ros-perception/vision_opencv.git
cd /home/ubuntu/ros2_ws
colcon build --symlink-install

# Configure environment for ubuntu user
echo "source /home/ubuntu/ros2_ws/install/setup.bash" >> /home/ubuntu/.bashrc
echo "export ROS_DOMAIN_ID=42" >> /home/ubuntu/.bashrc
chown -R ubuntu:ubuntu /home/ubuntu

# Install additional development tools
apt-get install -y git vim htop build-essential cmake pkg-config

# Create Jupyter service
echo "Setting up Jupyter..."
cat > /etc/systemd/system/jupyter.service << 'JUPYTER_EOF'
[Unit]
Description=Jupyter Notebook
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment=PATH=/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/home/ubuntu/.local/bin/jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token='' --NotebookApp.password=''
Restart=always

[Install]
WantedBy=multi-user.target
JUPYTER_EOF

systemctl enable jupyter
systemctl start jupyter

# Create validation script
cat > /home/ubuntu/validate-setup.sh << 'VALIDATE_EOF'
#!/bin/bash
echo "Robotics Environment Validation"
echo "=============================="

# Check NVIDIA drivers
if nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA drivers installed"
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits
else
    echo "✗ NVIDIA drivers not working"
fi

# Check CUDA
if command -v nvcc &> /dev/null; then
    echo "✓ CUDA installed"
    nvcc --version | head -1
else
    echo "✗ CUDA not found"
fi

# Check ROS 2
if [ -f /opt/ros/humble/setup.bash ]; then
    echo "✓ ROS 2 Humble installed"
    source /opt/ros/humble/setup.bash
    ros2 --version
else
    echo "✗ ROS 2 not found"
fi

# Check ROS 2 workspace
if [ -f /home/ubuntu/ros2_ws/install/setup.bash ]; then
    echo "✓ ROS 2 workspace built"
else
    echo "✗ ROS 2 workspace not built"
fi

# Check Python packages
python3 -c "import torch; print(f'✓ PyTorch {torch.__version__}')" 2>/dev/null || echo "✗ PyTorch not found"
python3 -c "import tensorflow as tf; print(f'✓ TensorFlow {tf.__version__}')" 2>/dev/null || echo "✗ TensorFlow not found"

echo ""
echo "GPU Status:"
nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits
VALIDATE_EOF

chmod +x /home/ubuntu/validate-setup.sh
chown ubuntu:ubuntu /home/ubuntu/validate-setup.sh

# Create startup scripts for common tasks
cat > /home/ubuntu/start-gazebo.sh << 'GAZEBO_EOF'
#!/bin/bash
echo "Starting Gazebo with empty world..."
source /opt/ros/humble/setup.bash
source /home/ubuntu/ros2_ws/install/setup.bash
gazebo --verbose &
echo "Gazebo started. Connect with:"
echo "gz client --gui-compressed"
GAZEBO_EOF

chmod +x /home/ubuntu/start-gazebo.sh
chown ubuntu:ubuntu /home/ubuntu/start-gazebo.sh

# Setup complete notification
echo "Robotics development environment setup complete!"
echo "SSH into the instance and run /home/ubuntu/validate-setup.sh to verify installation."
EOF

    print_success "User data script created"
}

# Launch spot instance
launch_spot_instance() {
    print_status "Launching g5.2xlarge spot instance..."

    # Read security group ID
    if [[ -f /tmp/robotics_sg_id.txt ]]; then
        SG_ID=$(cat /tmp/robotics_sg_id.txt)
    else
        SG_ID=$(aws ec2 describe-security-groups \
            --group-names "$SECURITY_GROUP_NAME" \
            --region "$REGION" \
            --query 'SecurityGroups[0].GroupId' \
            --output text)
    fi

    # Create launch specification
    cat > /tmp/spot-launch-spec.json << EOF
{
  "ImageId": "$AMI_ID",
  "InstanceType": "$INSTANCE_TYPE",
  "KeyName": "$KEY_NAME",
  "SecurityGroupIds": ["$SG_ID"],
  "SubnetId": "$(aws ec2 describe-subnets --region "$REGION" --query 'Subnets[0].SubnetId' --output text)",
  "IamInstanceProfile": {
    "Name": "$IAM_INSTANCE_PROFILE"
  },
  "UserData": "$(base64 -w 0 /tmp/robotics-user-data.sh)",
  "BlockDeviceMappings": [
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "VolumeSize": 100,
        "VolumeType": "gp3",
        "DeleteOnTermination": true
      }
    }
  ],
  "TagSpecifications": [
    {
      "ResourceType": "instance",
      "Tags": [
        {
          "Key": "Name",
          "Value": "$INSTANCE_NAME"
        },
        {
          "Key": "Project",
          "Value": "$PROJECT_TAG"
        },
        {
          "Key": "Owner",
          "Value": "$(aws sts get-caller-identity --query 'UserId' --output text)"
        }
      ]
    }
  ]
}
EOF

    # Request spot instance
    print_status "Requesting spot instance with max price: \$$SPOT_PRICE"
    SPOT_REQUEST_ID=$(aws ec2 request-spot-instances \
        --spot-price "$SPOT_PRICE" \
        --instance-count 1 \
        --type "persistent" \
        --launch-specification file:///tmp/spot-launch-spec.json \
        --region "$REGION" \
        --query 'SpotInstanceRequests[0].SpotInstanceRequestId' \
        --output text)

    print_success "Spot instance requested: $SPOT_REQUEST_ID"

    # Wait for instance to be launched
    print_status "Waiting for instance to be fulfilled..."

    while true; do
        STATUS=$(aws ec2 describe-spot-instance-requests \
            --spot-instance-request-ids "$SPOT_REQUEST_ID" \
            --region "$REGION" \
            --query 'SpotInstanceRequests[0].Status.Code' \
            --output text)

        echo "Current status: $STATUS"

        if [[ "$STATUS" == "fulfilled" ]]; then
            INSTANCE_ID=$(aws ec2 describe-spot-instance-requests \
                --spot-instance-request-ids "$SPOT_REQUEST_ID" \
                --region "$REGION" \
                --query 'SpotInstanceRequests[0].InstanceId' \
                --output text)
            print_success "Instance launched: $INSTANCE_ID"
            break
        elif [[ "$STATUS" == "price-too-low" || "$STATUS" == "capacity-not-available" ]]; then
            print_error "Spot request failed: $STATUS"
            print_status "Trying on-demand instance as fallback..."
            launch_on_demand_instance
            return
        fi

        sleep 10
    done

    # Wait for instance to be running
    print_status "Waiting for instance to be in running state..."
    aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"

    # Get instance details
    INSTANCE_IP=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)

    INSTANCE_DNS=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].PublicDnsName' \
        --output text)

    # Save instance information
    cat > /tmp/instance_info.txt << EOF
Instance ID: $INSTANCE_ID
Public IP: $INSTANCE_IP
Public DNS: $INSTANCE_DNS
Region: $REGION
SSH Command: ssh -i ~/.ssh/$KEY_NAME ubuntu@$INSTANCE_IP

Jupyter URL: http://$INSTANCE_IP:8888
EOF

    print_success "Instance is ready!"
    print_status "Instance details saved to /tmp/instance_info.txt"
}

# Fallback: Launch on-demand instance
launch_on_demand_instance() {
    print_status "Launching on-demand instance (fallback)..."

    # Read security group ID
    if [[ -f /tmp/robotics_sg_id.txt ]]; then
        SG_ID=$(cat /tmp/robotics_sg_id.txt)
    else
        SG_ID=$(aws ec2 describe-security-groups \
            --group-names "$SECURITY_GROUP_NAME" \
            --region "$REGION" \
            --query 'SecurityGroups[0].GroupId' \
            --output text)
    fi

    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id "$AMI_ID" \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-group-ids "$SG_ID" \
        --subnet-id "$(aws ec2 describe-subnets --region "$REGION" --query 'Subnets[0].SubnetId' --output text)" \
        --iam-instance-profile "Name=$IAM_INSTANCE_PROFILE" \
        --user-data file:///tmp/robotics-user-data.sh \
        --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":100,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME},{Key=Project,Value=$PROJECT_TAG}]" \
        --region "$REGION" \
        --query 'Instances[0].InstanceId' \
        --output text)

    print_success "On-demand instance launched: $INSTANCE_ID"

    # Wait for instance to be running
    aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"

    # Get instance details
    INSTANCE_IP=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)

    INSTANCE_DNS=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].PublicDnsName' \
        --output text)

    # Save instance information
    cat > /tmp/instance_info.txt << EOF
Instance ID: $INSTANCE_ID
Public IP: $INSTANCE_IP
Public DNS: $INSTANCE_DNS
Region: $REGION
SSH Command: ssh -i ~/.ssh/$KEY_NAME ubuntu@$INSTANCE_IP

Jupyter URL: http://$INSTANCE_IP:8888
EOF

    print_success "Instance is ready!"
    print_status "Instance details saved to /tmp/instance_info.txt"
}

# Display connection information
display_connection_info() {
    print_success "Robotics Development Instance Setup Complete!"
    echo ""
    echo "Connection Information:"
    echo "======================"

    if [[ -f /tmp/instance_info.txt ]]; then
        cat /tmp/instance_info.txt
    fi

    echo ""
    echo "Next Steps:"
    echo "==========="
    echo "1. SSH into the instance:"
    echo "   ssh -i ~/.ssh/$KEY_NAME ubuntu@<INSTANCE_IP>"
    echo ""
    echo "2. Wait for setup to complete (check logs):"
    echo "   tail -f /var/log/user-data.log"
    echo ""
    echo "3. Validate installation:"
    echo "   ~/validate-setup.sh"
    echo ""
    echo "4. Start development:"
    echo "   source /opt/ros/humble/setup.bash"
    echo "   source ~/ros2_ws/install/setup.bash"
    echo ""
    echo "5. Access Jupyter Notebook:"
    echo "   http://<INSTANCE_IP>:8888"
    echo ""
    echo "Cost Information:"
    echo "================="
    echo "Spot Instance: ~\$0.25-0.50/hour (when available)"
    echo "On-Demand: ~\$1.006-2.112/hour (fallback)"
    echo "Estimated monthly cost (10 hours/week):"
    echo "  Spot: ~\$40/month"
    echo "  On-Demand: ~\$43/month (us-east-1)"
    echo ""
    echo "Instance Management:"
    echo "===================="
    echo "To stop instance: aws ec2 stop-instances --instance-ids <INSTANCE_ID> --region $REGION"
    echo "To start instance: aws ec2 start-instances --instance-ids <INSTANCE_ID> --region $REGION"
    echo "To terminate instance: aws ec2 terminate-instances --instance-ids <INSTANCE_ID> --region $REGION"
    echo ""
}

# Cleanup function
cleanup() {
    print_status "Cleaning up temporary files..."
    rm -f /tmp/instance-trust-policy.json
    rm -f /tmp/spot-launch-spec.json
    rm -f /tmp/robotics-user-data.sh
    rm -f /tmp/robotics_sg_id.txt
}

# Main execution
main() {
    echo "AWS Robotics Instance Launcher"
    echo "=============================="
    echo "Instance Type: $INSTANCE_TYPE"
    echo "Region: $REGION"
    echo "Max Spot Price: \$$SPOT_PRICE/hour"
    echo ""

    # Set trap for cleanup
    trap cleanup EXIT

    # Check if user wants to continue
    read -p "This will launch a g5.2xlarge instance for robotics development. Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Instance launch cancelled."
        exit 0
    fi

    # Execute setup steps
    check_prerequisites
    create_ssh_key
    create_security_group
    create_iam_role
    create_user_data
    launch_spot_instance
    display_connection_info

    print_success "Setup complete! Instance details saved above."
}

# Run main function
main "$@"