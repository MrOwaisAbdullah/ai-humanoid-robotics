# AWS g5.2xlarge Robotics Instance Setup

This directory contains automated scripts for launching AWS g5.2xlarge instances optimized for Physical AI and humanoid robotics development.

## Files Overview

### `launch-robotics-instance.sh`
Comprehensive automation script that:
- Creates SSH key pair for secure access
- Sets up security groups with proper port configurations
- Creates IAM role with necessary permissions
- Launches g5.2xlarge spot instance (with on-demand fallback)
- Installs complete robotics development stack via user data
- Provides connection information and next steps

## Quick Start

### Prerequisites

1. **AWS CLI Installation**
   ```bash
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install

   # Configure AWS credentials
   aws configure
   ```

2. **Required AWS Permissions**
   - EC2: Create, start, stop, terminate instances
   - IAM: Create roles and instance profiles
   - VPC: Create security groups
   - S3: Access for data storage (optional)

3. **Install Additional Tools**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y jq

   # macOS
   brew install jq

   # Other systems
   # Download from: https://stedolan.github.io/jq/download/
   ```

### Instance Launch

1. **Download the script**
   ```bash
   wget https://your-domain.com/hardware-guides/aws-setup/launch-robotics-instance.sh
   chmod +x launch-robotics-instance.sh
   ```

2. **Run the launcher**
   ```bash
   ./launch-robotics-instance.sh
   ```

3. **Follow the prompts** - The script will:
   - Check prerequisites
   - Create necessary AWS resources
   - Launch the instance
   - Provide connection details

## Instance Configuration

### Hardware Specifications

**g5.2xlarge Instance:**
- **vCPU**: 8 AMD EPYC processors
- **Memory**: 32 GB RAM
- **GPU**: NVIDIA A10G (24 GB VRAM)
- **Storage**: 100 GB NVMe SSD (configurable)
- **Network**: Up to 25 Gbps
- **Architecture**: x86_64

### NVIDIA A10G GPU Detailed Specifications

**GPU Architecture:**
- **Architecture**: Ampere
- **CUDA Cores**: 24,576
- **Tensor Cores**: 384
- **GPU Memory**: 24 GB GDDR6
- **Memory Bandwidth**: 600 GB/s
- **Memory Interface**: 384-bit

**Performance Metrics:**
- **FP32 Performance**: 31.2 TFLOPS
- **FP16 Performance**: 624 TOPS
- **INT8 Performance**: 1,248 TOPS
- **Power Consumption**: 150W
- **Virtualization Support**: Yes (NVIDIA vGPU technology)

**Robotics Development Benefits:**
- High memory bandwidth (600 GB/s) for large simulation workloads
- Tensor cores accelerate ML model training for perception systems
- 24 GB VRAM supports complex 3D environments and sensor processing
- FP16/INT8 performance optimized for edge deployment scenarios

### Software Stack Installed

**Operating System:**
- Ubuntu 22.04 LTS

**NVIDIA Stack:**
- NVIDIA Drivers (535+)
- CUDA Toolkit 12.2
- cuDNN for deep learning

**Robotics Framework:**
- ROS 2 Humble (LTS)
- Gazebo 11 simulation
- Essential ROS packages

**Python Environment:**
- Python 3.10 with virtual environment
- PyTorch (GPU enabled)
- TensorFlow (GPU enabled)
- OpenCV, NumPy, SciPy, Matplotlib
- Jupyter Notebook

**Development Tools:**
- Git, Vim, Htop
- Build tools (GCC, CMake, Make)
- SSH access configured

### Security Configuration

**Security Group Rules:**
- **Port 22 (SSH)**: Remote command line access
- **Port 8888 (Jupyter)**: Web-based development environment
- **Port 80/443 (HTTP/HTTPS)**: Web applications
- **Port 11345 (Gazebo)**: Simulation communication

**IAM Permissions:**
- S3 full access (for data storage)
- EC2 management (for instance operations)

## Cost Management

### Pricing Information

**Spot Instance (Recommended):**
- **Cost**: ~$0.25-0.50/hour
- **Savings**: 60-80% off on-demand pricing
- **Risk**: Instance can be interrupted with 2-minute notice

**On-Demand (Fallback):**
- **Cost**: ~$1.006-2.112/hour (varies by region)
- **Guaranteed**: No interruption risk
- **Flexibility**: Start/stop anytime

**Monthly Estimates (10 hours/week):**
- **Spot**: ~$40/month
- **On-Demand**: ~$43/month (us-east-1)

### Cost Optimization Tips

1. **Use Spot Instances**: 60-80% savings when available
2. **Schedule Usage**: Stop instances when not in use
3. **Monitor Costs**: Set up AWS billing alerts
4. **Use Smaller Instances**: Consider g5.xlarge for lighter workloads
5. **Leverage Reserved Instances**: For long-term projects

## Usage Examples

### SSH Access
```bash
# Connect to instance
ssh -i ~/.ssh/robotics-key ubuntu@<INSTANCE_IP>

# Once connected
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
```

### Jupyter Notebook
```bash
# Access in browser
http://<INSTANCE_IP>:8888

# Or tunnel for security
ssh -L 8888:localhost:8888 ubuntu@<INSTANCE_IP>
# Then access http://localhost:8888
```

### ROS 2 Development
```bash
# Test ROS 2 installation
ros2 doctor

# Run a simple talker
ros2 run demo_nodes_cpp talker

# In another terminal
ros2 run demo_nodes_py listener
```

### Gazebo Simulation
```bash
# Start Gazebo
~/start-gazebo.sh

# Or manually
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
gazebo --verbose
```

### GPU Monitoring
```bash
# Check GPU status
nvidia-smi

# Monitor utilization
watch -n 1 nvidia-smi
```

## Instance Management

### Start/Stop Instance
```bash
# Stop instance (data preserved)
aws ec2 stop-instances --instance-ids <INSTANCE_ID> --region us-east-1

# Start stopped instance
aws ec2 start-instances --instance-ids <INSTANCE_ID> --region us-east-1

# Terminate instance (data lost)
aws ec2 terminate-instances --instance-ids <INSTANCE_ID> --region us-east-1
```

### Backup Data
```bash
# Create backup of workspace
tar -czf ros2_workspace_backup.tar.gz ~/ros2_ws

# Upload to S3
aws s3 cp ros2_workspace_backup.tar.gz s3://your-backup-bucket/
```

### Monitoring
```bash
# Check instance status
aws ec2 describe-instances --instance-ids <INSTANCE_ID>

# Monitor costs
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31
```

## Troubleshooting

### Common Issues

**Instance Not Responding:**
```bash
# Check instance status
aws ec2 describe-instances --instance-ids <INSTANCE_ID>

# Check system logs
aws ec2 get-console-output --instance-ids <INSTANCE_ID>
```

**SSH Connection Failed:**
```bash
# Check security group
aws ec2 describe-security-groups --group-names robotics-sg

# Verify key pair
aws ec2 describe-key-pairs --key-names robotics-key
```

**GPU Not Detected:**
```bash
# SSH into instance and check
nvidia-smi

# Reboot if necessary
sudo reboot
```

**Spot Instance Interrupted:**
- Script automatically falls back to on-demand
- Data is preserved on EBS volume
- Can relaunch spot instance when capacity available

### Performance Issues

**Low GPU Utilization:**
```python
# Check PyTorch GPU usage
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

# Enable GPU acceleration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
```

**Memory Constraints:**
```bash
# Check memory usage
free -h
df -h

# Clean up if needed
sudo apt-get autoremove
conda clean --all
```

## Advanced Configuration

### Custom Instance Types

**Light Workloads (g5.xlarge):**
- Cost: ~$0.50/hour spot
- GPU: Same A10G (24GB)
- CPU: 4 cores
- RAM: 16GB

**Heavy Workloads (g5.4xlarge):**
- Cost: ~$1.00/hour spot
- GPU: Same A10G (24GB)
- CPU: 16 cores
- RAM: 64GB

### Custom AMIs

Create custom AMI with pre-installed software:
```bash
# Create AMI from running instance
aws ec2 create-image \
  --instance-id <INSTANCE_ID> \
  --name "robotics-custom-ami" \
  --description "Custom AMI for robotics development"
```

### Multiple Instance Setup

For team environments, consider:
- VPC peering for instance communication
- Shared S3 buckets for data storage
- IAM roles for resource sharing
- CloudFormation for infrastructure as code

## Integration with Course

### Access Course Materials
```bash
# Clone course repository
git clone https://github.com/your-org/physical-ai-course.git

# Mount from S3
aws s3 sync s3://robotics-course-materials/ ~/course-materials/
```

### Submitting Work
```bash
# Backup completed work
aws s3 sync ~/ros2_ws s3://your-submission-bucket/student-work/
```

### Collaboration Tools
- Use VNC for shared desktop environments
- Set up SSH tunnels for secure collaboration
- Configure GitHub integration with AWS CodeCommit

## Security Best Practices

1. **SSH Key Management**: Use unique keys for each user
2. **Network Security**: Restrict IP ranges when possible
3. **Data Encryption**: Use EBS encryption for sensitive data
4. **Access Control**: Use IAM roles instead of access keys
5. **Regular Updates**: Keep system packages updated
6. **Monitoring**: Set up CloudWatch alerts for unusual activity

## Support and Documentation

- **AWS Documentation**: https://docs.aws.amazon.com/
- **ROS 2 Documentation**: https://docs.ros.org/en/humble/
- **CUDA Documentation**: https://docs.nvidia.com/cuda/
- **Course Support**: Available through learning platform forums

## Version History

- **v1.0** (2025-12-04): Initial release with complete automation
- **v1.1** (Planned): Add multi-region support
- **v1.2** (Planned): Add custom configuration options

---

**Note**: This script is designed for educational purposes in the Physical AI course. Production usage may require additional security and compliance considerations.