#!/usr/bin/env python3

import os
import subprocess
import sys
import logging
from pathlib import Path
import shutil
import tempfile
import platform


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ClangVersion:
    """Helper class to parse and compare clang versions."""

    def __init__(self, version_str: str):
        # Extract version number from strings like "clang version 14.0.0" or "Apple clang version 14.0.0"
        parts = version_str.split('version')[1].strip().split('.')
        self.major = int(parts[0])
        self.minor = int(parts[1]) if len(parts) > 1 else 0

    def __ge__(self, other):
        if self.major != other.major:
            return self.major >= other.major
        return self.minor >= other.minor


class EnvironmentSetup:
    """Setup development environment for C source generation."""

    def __init__(self, install_dir: str = None):
        self.install_dir = install_dir or str(Path.home() / "work")
        self.csmith_dir = os.path.join(self.install_dir, "csmith")
        self.os_type = platform.system()
        self.min_clang_version = ClangVersion("version 10.0.0")  # Minimum required version

        # Define packages excluding clang (will be installed only if needed)
        self.base_packages = {
            'Darwin': [
                "cmake", "m4", "git", "boost"
            ],
            'Linux': [
                "cmake", "m4", "git", "build-essential",
                "libboost-all-dev"
            ]
        }

        self.clang_packages = {
            'Darwin': ["llvm"],
            'Linux': ["clang", "llvm"]
        }

    def check_clang_installation(self) -> tuple[bool, str]:
        """
        Check if a suitable clang installation exists.
        Returns: (is_suitable, path_to_clang)
        """
        try:
            # Check system clang
            system_clang = shutil.which("clang")
            if system_clang:
                result = subprocess.run([system_clang, "--version"],
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    version = ClangVersion(result.stdout)
                    if version >= self.min_clang_version:
                        logging.info(f"Found suitable system clang: {system_clang}")
                        return True, system_clang

            # Check brew-installed clang on macOS
            if self.os_type == 'Darwin':
                brew_clang = "/usr/local/opt/llvm/bin/clang"
                if os.path.exists(brew_clang):
                    result = subprocess.run([brew_clang, "--version"],
                                            capture_output=True, text=True)
                    if result.returncode == 0:
                        version = ClangVersion(result.stdout)
                        if version >= self.min_clang_version:
                            logging.info(f"Found suitable Homebrew clang: {brew_clang}")
                            return True, brew_clang

            logging.info("No suitable clang installation found")
            return False, ""

        except Exception as e:
            logging.error(f"Error checking clang installation: {e}")
            return False, ""

    def install_packages(self) -> bool:
        """Install required system packages."""
        try:
            packages_to_install = self.base_packages[self.os_type].copy()

            # Check if we need to install clang
            has_clang, _ = self.check_clang_installation()
            if not has_clang:
                logging.info("Will install clang as no suitable version was found")
                packages_to_install.extend(self.clang_packages[self.os_type])

            if self.os_type == 'Darwin':
                logging.info("Updating Homebrew...")
                subprocess.run(["brew", "update"], check=True)

                logging.info("Installing required packages...")
                for package in packages_to_install:
                    subprocess.run(["brew", "install", package], check=True)

            elif self.os_type == 'Linux':
                logging.info("Updating package list...")
                subprocess.run(["sudo", "apt-get", "update"], check=True)

                logging.info("Installing required packages...")
                cmd = ["sudo", "apt-get", "install", "-y"] + packages_to_install
                subprocess.run(cmd, check=True)

            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install packages: {e}")
            return False

    def create_config(self) -> bool:
        """Create configuration file for the generator."""
        try:
            # Use existing clang if suitable, otherwise use newly installed one
            has_clang, clang_path = self.check_clang_installation()
            if not has_clang:
                if self.os_type == 'Darwin':
                    clang_path = "/usr/local/opt/llvm/bin/clang"
                else:
                    clang_path = shutil.which("clang")

            if not clang_path:
                raise Exception("Could not find clang installation")

            config = {
                "CSMITH_PATH": os.path.join(self.csmith_dir, "build/src/csmith"),
                "CLANG_PATH": clang_path,
                "CSMITH_RUNTIME": os.path.join(self.csmith_dir, "runtime")
            }

            with open("generator_config.json", "w") as f:
                import json
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Failed to create config file: {e}")
            return False

    def verify_installation(self) -> bool:
        """Verify that the installation was successful."""
        try:
            # Check csmith
            csmith_path = os.path.join(self.csmith_dir, "build/src/csmith")
            subprocess.run([csmith_path, "--version"],
                           check=True, capture_output=True)

            # Check clang
            if self.os_type == 'Darwin':
                clang_cmd = "/usr/local/opt/llvm/bin/clang"
                if not os.path.exists(clang_cmd):
                    clang_cmd = "clang"
            else:
                clang_cmd = "clang"

            subprocess.run([clang_cmd, "--version"],
                           check=True, capture_output=True)

            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Installation verification failed: {e}")
            return False

    def setup_environment_vars(self):
        """Setup environment variables if needed."""
        if self.os_type == 'Darwin':
            # Add LLVM to PATH for macOS
            llvm_bin = "/usr/local/opt/llvm/bin"
            if os.path.exists(llvm_bin):
                current_path = os.environ.get('PATH', '')
                if llvm_bin not in current_path:
                    os.environ['PATH'] = f"{llvm_bin}:{current_path}"
                    logging.info(f"Added {llvm_bin} to PATH")


def main():
    setup = EnvironmentSetup()

    if not setup.check_prerequisites():
        sys.exit(1)

    if not setup.install_packages():
        sys.exit(1)

    if not setup.setup_csmith():
        sys.exit(1)

    if not setup.create_config():
        sys.exit(1)

    if setup.verify_installation():
        logging.info("Environment setup completed successfully!")
    else:
        logging.error("Environment setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
