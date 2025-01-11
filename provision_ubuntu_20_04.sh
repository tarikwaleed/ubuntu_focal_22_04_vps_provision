#!/bin/bash

# Logging setup
LOG_FILE="/var/log/docker-install.log"
exec 1> >(tee -a "$LOG_FILE") 2>&1

echo "Starting installation process..."
echo "Installation logs will be saved to $LOG_FILE"

# Function to check if a command was successful
check_status() {
    if [ $? -eq 0 ]; then
        echo "✓ $1 successful"
    else
        echo "✗ $1 failed. Check $LOG_FILE for details"
        exit 1
    fi
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Check if system is Ubuntu
if [ ! -f /etc/os-release ] || ! grep -q "ubuntu" /etc/os-release; then
    echo "This script is designed for Ubuntu only"
    exit 1
fi

# Update system packages
echo "Updating system packages..."
apt-get update && apt-get upgrade -y
check_status "System update"

# Install prerequisites
echo "Installing prerequisites..."
apt install -y curl wget git apt-transport-https ca-certificates software-properties-common
check_status "Prerequisites installation"

# Install Docker if not already installed
if ! command -v docker &>/dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    check_status "Docker installation"

    # Start and enable Docker service
    systemctl start docker
    systemctl enable docker
    check_status "Docker service activation"

    # Add current user to docker group
    usermod -aG docker $SUDO_USER
    check_status "User group modification"
else
    echo "Docker is already installed"
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &>/dev/null; then
    echo "Installing Docker Compose..."
    apt install -y docker-compose
    check_status "Docker Compose installation"
else
    echo "Docker Compose is already installed"
fi

# Wait for Docker to be fully started
echo "Waiting for Docker service to be fully active..."
for i in {1..30}; do
    if systemctl is-active --quiet docker; then
        echo "Docker service is active"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Docker service failed to start"
        exit 1
    fi
    sleep 1
done

# Install NGinX Proxy Manager
echo "Installing NGinX Proxy Manager..."
mkdir -p ~/docker/nginx-proxy-manager
cd ~/docker/nginx-proxy-manager

# Create docker-compose file for NPM
cat > docker-compose.yml <<EOF
version: '3'
services:
  app:
    image: 'jc21/nginx-proxy-manager:latest'
    restart: always
    ports:
      - '80:80'
      - '81:81'
      - '443:443'
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt
EOF

# Start NGinX Proxy Manager
docker-compose up -d
check_status "NGinX Proxy Manager installation"

# Install Portainer
echo "Installing Portainer-CE..."
docker volume create portainer_data
docker run -d \
    -p 8000:8000 \
    -p 9000:9000 \
    --name=portainer \
    --restart=always \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v portainer_data:/data \
    portainer/portainer-ce
check_status "Portainer installation"

# Print installation summary
echo ""
echo "=== Installation Complete ==="
echo ""
echo "The following services have been installed:"
echo "1. Docker"
echo "2. Docker Compose"
echo "3. NGinX Proxy Manager"
echo "   - URL: http://your-server-ip:81"
echo "   - Default credentials:"
echo "     Email: admin@example.com"
echo "     Password: changeme"
echo ""
echo "4. Portainer-CE"
echo "   - URL: http://your-server-ip:9000"
echo "   - Create your admin account on first login"
echo ""
echo "Important Notes:"
echo "- Log out and back in to use Docker without sudo"
echo "- Change the default passwords for both NGinX Proxy Manager and Portainer"
echo "- Installation logs are available in $LOG_FILE"