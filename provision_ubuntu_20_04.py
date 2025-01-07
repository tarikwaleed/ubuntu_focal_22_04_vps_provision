#!/usr/bin/env python3

import os
import sys
import time
import subprocess
from typing import Optional


def run_command(command: str, log_file: str = "docker-script-install.log") -> tuple[int, str]:
    """Run shell command and log output."""
    print(f"Running: {command}")
    with open(log_file, 'a') as f:
        process = subprocess.run(
            command,
            shell=True,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True
        )
    return process.returncode, process.stdout


def show_spinner(seconds: int):
    """Show a spinner for the specified number of seconds."""
    spin = '-\\|/'
    for _ in range(seconds * 10):
        for char in spin:
            sys.stdout.write(f'\r{char}')
            sys.stdout.flush()
            time.sleep(0.1)
    sys.stdout.write('\r')


def is_docker_active() -> bool:
    """Check if Docker service is active."""
    result = subprocess.run(
        ["systemctl", "is-active", "docker"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip() == "active"


def is_docker_compose_installed() -> bool:
    """Check if Docker Compose is installed."""
    result = subprocess.run(
        ["which", "docker-compose"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def check_ubuntu_version() -> Optional[str]:
    """Check if the system is Ubuntu and return version."""
    try:
        with open('/etc/os-release', 'r') as f:
            os_info = dict(line.strip().split('=', 1) for line in f if '=' in line)

        if os_info.get('ID', '').lower() == 'ubuntu':
            version = os_info.get('VERSION_ID', '').strip('"')
            return version
        return None
    except:
        return None


class UbuntuDockerInstaller:
    def install_docker_packages(self):
        """Install Docker and Docker Compose."""
        print("\n=== Installing Docker and Docker Compose ===")

        # Update system
        print("\nUpdating system packages...")
        run_command("apt update && apt upgrade -y")
        show_spinner(3)

        # Install prerequisites
        print("\nInstalling prerequisites...")
        run_command("apt install curl wget git -y")

        # Install Docker if not already installed
        if not is_docker_active():
            print("\nInstalling Docker-CE...")
            run_command("curl -fsSL https://get.docker.com | sh")
            run_command("usermod -aG docker $USER")
            run_command("systemctl start docker")
            run_command("systemctl enable docker")
            print("\nNOTE: You'll need to log out and back in for the docker group changes to take effect.")

        # Install Docker Compose if not already installed
        if not is_docker_compose_installed():
            print("\nInstalling Docker-Compose...")
            run_command("apt install docker-compose -y")

    def install_nginx_proxy_manager(self):
        """Install NGinX Proxy Manager."""
        print("\n=== Installing NGinX Proxy Manager ===")
        os.makedirs("docker/nginx-proxy-manager", exist_ok=True)
        os.chdir("docker/nginx-proxy-manager")

        print("\nDownloading and starting NGinX Proxy Manager...")
        run_command(
            "curl https://gitlab.com/bmcgonag/docker_installs/-/raw/main/docker_compose.nginx_proxy_manager.yml -o docker-compose.yml")
        run_command("docker-compose up -d")

        print("\nNGinX Proxy Manager installed!")
        print("Access it at: http://your-server-ip:81")
        print("Default login credentials:")
        print("    Username: admin@example.com")
        print("    Password: changeme")

        os.chdir(os.path.expanduser("~"))

    def install_portainer(self):
        """Install Portainer-CE."""
        print("\n=== Installing Portainer-CE ===")
        run_command("docker volume create portainer_data")
        run_command(
            "docker run -d -p 8000:8000 -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce")

        print("\nPortainer-CE installed!")
        print("Access it at: http://your-server-ip:9000")
        print("Create your admin account on first login.")

    def main(self):
        """Main installation process."""
        # Check Ubuntu version
        ubuntu_version = check_ubuntu_version()
        if not ubuntu_version:
            print("Error: This script is designed to work only on Ubuntu.")
            print("Your system appears to be running a different distribution.")
            sys.exit(1)

        print(f"\nUbuntu {ubuntu_version} detected.")
        print("\nStarting automated installation process...")

        # Install everything in sequence
        self.install_docker_packages()

        # Wait for Docker to be fully started
        print("\nWaiting for Docker service to be fully started...")
        retries = 0
        while not is_docker_active() and retries < 30:
            time.sleep(1)
            retries += 1

        if not is_docker_active():
            print("Error: Docker service failed to start properly.")
            sys.exit(1)

        # Install additional services
        self.install_nginx_proxy_manager()
        self.install_portainer()

        print("\n=== Installation Complete ===")
        print("\nServices installed:")
        print("1. Docker")
        print("2. Docker Compose")
        print("3. NGinX Proxy Manager (http://your-server-ip:81)")
        print("4. Portainer-CE (http://your-server-ip:9000)")
        print("\nPlease make sure to:")
        print("1. Log out and back in to use Docker without sudo")
        print("2. Configure NGinX Proxy Manager with the default credentials")
        print("3. Set up your Portainer admin account")


if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run as root (sudo)")
        sys.exit(1)

    installer = UbuntuDockerInstaller()
    installer.main()
