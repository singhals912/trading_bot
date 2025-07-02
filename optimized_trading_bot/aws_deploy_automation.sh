#!/bin/bash

# AWS Trading Bot Deployment Automation Script
# This script automates the entire AWS EC2 deployment process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting AWS Trading Bot Deployment Automation${NC}"
echo "=================================================================="

# Configuration
REGION="us-east-1"
INSTANCE_TYPE="t3.micro"
KEY_NAME="trading-bot-key"
SECURITY_GROUP_NAME="trading-bot-sg"
INSTANCE_NAME="trading-bot-instance"

# Step 1: Check AWS CLI installation
echo -e "${BLUE}📋 Step 1: Checking AWS CLI installation...${NC}"
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Installing...${NC}"
    
    # Install AWS CLI for macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install awscli
        else
            echo "Please install Homebrew first, then run: brew install awscli"
            exit 1
        fi
    else
        echo "Please install AWS CLI: https://aws.amazon.com/cli/"
        exit 1
    fi
fi

echo -e "${GREEN}✅ AWS CLI is installed${NC}"

# Step 2: Check AWS credentials
echo -e "${BLUE}📋 Step 2: Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${YELLOW}⚠️ AWS credentials not configured${NC}"
    echo "Please run: aws configure"
    echo "You'll need:"
    echo "  - AWS Access Key ID"
    echo "  - AWS Secret Access Key"
    echo "  - Default region (us-east-1)"
    echo "  - Default output format (json)"
    
    read -p "Press Enter after configuring AWS credentials..."
    
    # Verify again
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials still not working. Please check your configuration.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ AWS credentials configured${NC}"

# Step 3: Create key pair
echo -e "${BLUE}📋 Step 3: Creating EC2 key pair...${NC}"
if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &> /dev/null; then
    echo -e "${YELLOW}⚠️ Key pair '$KEY_NAME' already exists${NC}"
else
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --region "$REGION" \
        --query 'KeyMaterial' \
        --output text > ~/Downloads/${KEY_NAME}.pem
    
    chmod 600 ~/Downloads/${KEY_NAME}.pem
    echo -e "${GREEN}✅ Key pair created: ~/Downloads/${KEY_NAME}.pem${NC}"
fi

# Step 4: Create security group
echo -e "${BLUE}📋 Step 4: Creating security group...${NC}"
VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)

if aws ec2 describe-security-groups --group-names "$SECURITY_GROUP_NAME" --region "$REGION" &> /dev/null; then
    echo -e "${YELLOW}⚠️ Security group '$SECURITY_GROUP_NAME' already exists${NC}"
    SG_ID=$(aws ec2 describe-security-groups --group-names "$SECURITY_GROUP_NAME" --region "$REGION" --query 'SecurityGroups[0].GroupId' --output text)
else
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SECURITY_GROUP_NAME" \
        --description "Security group for trading bot" \
        --vpc-id "$VPC_ID" \
        --region "$REGION" \
        --query 'GroupId' \
        --output text)
    
    # Add ingress rules
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region "$REGION"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region "$REGION"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 8080 \
        --cidr 0.0.0.0/0 \
        --region "$REGION"
    
    echo -e "${GREEN}✅ Security group created: $SG_ID${NC}"
fi

# Step 5: Get latest Ubuntu 22.04 AMI
echo -e "${BLUE}📋 Step 5: Finding latest Ubuntu 22.04 AMI...${NC}"
AMI_ID=$(aws ec2 describe-images \
    --owners 099720109477 \
    --filters 'Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*' \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --region "$REGION" \
    --output text)

echo -e "${GREEN}✅ Latest Ubuntu 22.04 AMI: $AMI_ID${NC}"

# Step 6: Launch EC2 instance
echo -e "${BLUE}📋 Step 6: Launching EC2 instance...${NC}"

# Create user data script
cat > /tmp/user-data.sh << 'EOF'
#!/bin/bash
apt update
apt upgrade -y
apt install -y docker.io docker-compose git curl wget htop
systemctl start docker
systemctl enable docker
usermod -a -G docker ubuntu

# Install AWS CLI in instance
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Create trading bot directory
mkdir -p /opt/trading_bot
chown ubuntu:ubuntu /opt/trading_bot

# Create logs directory
mkdir -p /opt/trading_bot/logs
chown ubuntu:ubuntu /opt/trading_bot/logs
EOF

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --count 1 \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --user-data file:///tmp/user-data.sh \
    --region "$REGION" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo -e "${GREEN}✅ Instance launched: $INSTANCE_ID${NC}"

# Step 7: Wait for instance to be running
echo -e "${BLUE}📋 Step 7: Waiting for instance to be running...${NC}"
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
echo -e "${GREEN}✅ Instance is running${NC}"

# Step 8: Get public IP
echo -e "${BLUE}📋 Step 8: Getting instance public IP...${NC}"
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo -e "${GREEN}✅ Instance public IP: $PUBLIC_IP${NC}"

# Step 9: Wait for SSH to be ready
echo -e "${BLUE}📋 Step 9: Waiting for SSH to be ready...${NC}"
echo "This may take 2-3 minutes..."

for i in {1..30}; do
    if ssh -i ~/Downloads/${KEY_NAME}.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "echo 'SSH Ready'" &> /dev/null; then
        echo -e "${GREEN}✅ SSH is ready${NC}"
        break
    fi
    echo "Waiting for SSH... (attempt $i/30)"
    sleep 10
done

# Step 10: Create deployment configuration
echo -e "${BLUE}📋 Step 10: Creating deployment configuration...${NC}"

cat > aws_deployment_config.txt << EOF
# AWS Deployment Configuration
INSTANCE_ID=$INSTANCE_ID
PUBLIC_IP=$PUBLIC_IP
REGION=$REGION
KEY_FILE=~/Downloads/${KEY_NAME}.pem
SSH_COMMAND=ssh -i ~/Downloads/${KEY_NAME}.pem ubuntu@$PUBLIC_IP
DASHBOARD_URL=http://$PUBLIC_IP
EOF

echo -e "${GREEN}✅ Deployment configuration saved to aws_deployment_config.txt${NC}"

# Clean up temp files
rm -f /tmp/user-data.sh

echo ""
echo "=================================================================="
echo -e "${GREEN}🎉 AWS EC2 Instance Successfully Created!${NC}"
echo "=================================================================="
echo -e "${BLUE}Instance Details:${NC}"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  SSH Key: ~/Downloads/${KEY_NAME}.pem"
echo "  Region: $REGION"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Run: ./aws_setup_trading_bot.sh"
echo "  2. Access dashboard: http://$PUBLIC_IP"
echo ""
echo -e "${YELLOW}SSH Command:${NC}"
echo "  ssh -i ~/Downloads/${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
echo ""
echo -e "${GREEN}Ready for trading bot deployment!${NC}"