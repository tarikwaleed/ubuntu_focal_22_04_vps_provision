#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import platform
from typing import Optional

def run_command(command: str, log_file: str = "docker-script-install.log") -> tuple[int, str]:
    """Run shell command and log output."""
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

def get_system_info() -> dict:
    """Get system information using lsb_release."""
    try:
        info = {
            'distributor': subprocess.getoutput('lsb_release -i'),
            'description': subprocess.getoutput('lsb_release -d'),
            'release': subprocess.getoutput('lsb_release -r'),
            'codename': subprocess.getoutput('lsb_release -c')
        }
        return info
    except Exception:
        return {}

class DockerInstaller:
    def __init__(self):
        self.os_choice = None
        self.install_docker = False
        self.install_docker_compose = False
        self.install_npm = False
        self.install_navidrome = False
        self.install_portainer = False
        self.portainer_choice = None

    def prompt_installations(self):
        """Prompt user for what to install."""
        print("\nWe can install Docker-CE, Docker-Compose, NGinX Proxy Manager, and Portainer-CE.")
        print("Please select 'y' for each item you would like to install.")
        print("NOTE: Without Docker you cannot use Docker-Compose, NGinX Proxy Manager, or Portainer-CE.")
        print("      You also must have Docker-Compose for NGinX Proxy Manager to be installed.\n")

        if not is_docker_active():
            self.install_docker = input("Docker-CE (y/n): ").lower() == 'y'
        else:
            print("Docker appears to be installed and running.\n")

        if not is_docker_compose_installed():
            self.install_docker_compose = input("Docker-Compose (y/n): ").lower() == 'y'
        else:
            print("Docker-compose appears to be installed.\n")

        self.install_npm = input("NGinX Proxy Manager (y/n): ").lower() == 'y'
        self.install_navidrome = input("Navidrome (y/n): ").lower() == 'y'
        self.install_portainer = input("Portainer-CE (y/n): ").lower() == 'y'

        if self.install_portainer:
            print("\nPlease choose either Portainer-CE or just Portainer Agent:")
            print("1. Full Portainer-CE (Web GUI for Docker, Swarm, and Kubernetes)")
            print("2. Portainer Agent - Remote Agent to Connect from Portainer-CE")
            print("3. Nevermind -- I don't need Portainer after all.")

            while True:
                choice = input("Enter your choice (1-3): ")
                if choice in ['1', '2', '3']:
                    self.portainer_choice = int(choice)
                    break
                print("Invalid selection, please try again...")

    def install_debian_ubuntu(self):
        """Install for Debian/Ubuntu systems."""
        print("Installing System Updates... this may take a while...")
        run_command("apt update && apt upgrade -y")
        show_spinner(3)

        print("Installing Prerequisite Packages...")
        run_command("apt install curl wget git -y")

        if self.install_docker:
            print("Installing Docker-CE...")
            run_command("curl -fsSL https://get.docker.com | sh")
            run_command("usermod -aG docker $USER")

        if self.install_docker_compose:
            print("Installing Docker-Compose...")
            run_command("apt install docker-compose -y")

    def install_centos(self):
        """Install for CentOS systems."""
        if self.install_docker:
            print("Updating System Packages...")
            run_command("yum check-update")

            print("Installing Prerequisite Packages...")
            run_command("dnf install git curl wget -y")

            print("Installing Docker-CE...")
            run_command("curl -fsSL https://get.docker.com/ | sh")

            print("Starting and enabling Docker service...")
            run_command("systemctl start docker")
            run_command("systemctl enable docker")

        if self.install_docker_compose:
            print("Installing Docker-Compose...")
            run_command('curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose')
            run_command("chmod +x /usr/local/bin/docker-compose")

    def install_arch(self):
        """Install for Arch Linux systems."""
        if input("Do you want to install system updates prior to installing Docker-CE? (y/n): ").lower() == 'y':
            print("Installing System Updates...")
            run_command("pacman -Syu")
            show_spinner(3)

        print("Installing Prerequisite Packages...")
        run_command("pacman -Sy git curl wget")

        if self.install_docker:
            print("Installing Docker-CE...")
            run_command("curl -fsSL https://get.docker.com | sh")

        if self.install_docker_compose:
            print("Installing Docker-Compose...")
            run_command("pacman -Sy docker-compose")

    def install_nginx_proxy_manager(self):
        """Install NGinX Proxy Manager."""
        print("Installing NGinX Proxy Manager...")
        os.makedirs("docker/nginx-proxy-manager", exist_ok=True)
        os.chdir("docker/nginx-proxy-manager")

        run_command("curl https://gitlab.com/bmcgonag/docker_installs/-/raw/main/docker_compose.nginx_proxy_manager.yml -o docker-compose.yml")
        run_command("docker-compose up -d")

        print("\nNavigate to your server hostname / IP address on port 81 to setup")
        print("NGinX Proxy Manager admin account.")
        print("\nDefault login credentials:")
        print("    username: admin@example.com")
        print("    password: changeme")

        os.chdir(os.path.expanduser("~"))

    def install_portainer(self):
        """Install Portainer or Portainer Agent."""
        if self.portainer_choice == 1:
            print("Installing Portainer-CE...")
            run_command("docker volume create portainer_data")
            run_command("docker run -d -p 8000:8000 -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce")
            print("\nNavigate to your server hostname / IP address on port 9000 to create your admin account")

        elif self.portainer_choice == 2:
            print("Installing Portainer Agent...")
            run_command("docker volume create portainer_data")
            run_command("docker run -d -p 9001:9001 --name portainer_agent --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v /var/lib/docker/volumes:/var/lib/docker/volumes portainer/agent")
            print("\nAdd this Agent instance via the 'Endpoints' option in Portainer-CE")
            print("Use the IP address of this server and port 9001")

    def install_navidrome(self):
        """Install Navidrome."""
        print("Installing Navidrome...")
        os.makedirs("docker/navidrome", exist_ok=True)
        os.chdir("docker/navidrome")

        run_command("curl https://gitlab.com/bmcgonag/docker_installs/-/raw/main/docker_compose_navidrome.yml -o docker-compose.yml")
        run_command("docker-compose up -d")

        print("\nNavigate to your server hostname / IP address on port 4533 to setup")
        print("your new Navidrome admin account.")

        os.chdir(os.path.expanduser("~"))

    def main(self):
        """Main installation process."""
        system_info = get_system_info()
        print("\nSystem Information:")
        for key, value in system_info.items():
            print(f"    -- {key:<12} {value}")

        print("\nSelect your OS / distro:")
        print("1. CentOS 7 / 8 / Fedora")
        print("2. Debian 10 / 11")
        print("3. Ubuntu 18.04")
        print("4. Ubuntu 20.04 / 21.04 / 22.04")
        print("5. Arch Linux")
        print("6. Exit")

        while True:
            try:
                choice = int(input("\nEnter your choice (1-6): "))
                if 1 <= choice <= 6:
                    self.os_choice = choice
                    break
                print("Invalid selection, please try again...")
            except ValueError:
                print("Please enter a number between 1 and 6")

        if self.os_choice == 6:
            sys.exit(0)

        self.prompt_installations()

        # Perform installations based on OS choice
        if self.os_choice == 1:  # CentOS
            self.install_centos()
        elif self.os_choice in [2, 3, 4]:  # Debian/Ubuntu
            self.install_debian_ubuntu()
        elif self.os_choice == 5:  # Arch
            self.install_arch()

        # Install additional services if requested
        if self.install_npm:
            self.install_nginx_proxy_manager()
        if self.install_portainer and self.portainer_choice in [1, 2]:
            self.install_portainer()
        if self.install_navidrome:
            self.install_navidrome()

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run as root (sudo)")
        sys.exit(1)

    installer = DockerInstaller()
    installer.main()