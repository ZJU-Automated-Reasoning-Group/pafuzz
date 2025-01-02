"""
This script automates the setup process for building and installing dependencies for the Pafuzz project.

Functions:
    install_dependencies():
        Installs necessary build tools and dependencies based on the operating system.
        - On Linux: Installs build-essential, git, and cmake using apt-get.
        - On macOS: Installs cmake and git using Homebrew.

    clone_and_build_csmith():
        Clones the Csmith repository from GitHub if it does not already exist, and builds it using cmake and make.

    clone_and_build_yarpgen():
        Clones the YARPGen repository from GitHub if it does not already exist, and builds it using cmake and make.

Usage:
    Run this script directly to install dependencies and build the Csmith and YARPGen projects.

"""
import os
import platform
import subprocess


def install_dependencies():
    if platform.system() == "Linux":
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "-y", "build-essential", "git", "cmake"])
    elif platform.system() == "Darwin":
        subprocess.run(["brew", "update"])
        subprocess.run(["brew", "install", "cmake", "git"])

def clone_and_build_csmith():
    if not os.path.exists("csmith"):
        subprocess.run(["git", "clone", "https://github.com/csmith-project/csmith.git"])
    os.chdir("csmith")
    subprocess.run(["cmake", "."])
    subprocess.run(["make"])
    os.chdir("..")

def clone_and_build_yarpgen():
    if not os.path.exists("yarpgen"):
        subprocess.run(["git", "clone", "https://github.com/intel/yarpgen.git"])
    os.chdir("yarpgen")
    subprocess.run(["cmake", "."])
    subprocess.run(["make"])
    os.chdir("..")

if __name__ == "__main__":
    install_dependencies()
    clone_and_build_csmith()
    clone_and_build_yarpgen()
