import os
import platform
import subprocess
import sys
import tarfile
import shutil
import time
from pathlib import Path
import requests
from zipfile import ZipFile
from tqdm import tqdm


class ColorPrint:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def print_step(step_num, total_steps, message):
        print(f"{ColorPrint.BLUE}[Step {step_num}/{total_steps}] {message}{ColorPrint.ENDC}")

    @staticmethod
    def print_success(message):
        print(f"{ColorPrint.GREEN}✓ {message}{ColorPrint.ENDC}")

    @staticmethod
    def print_error(message):
        print(f"{ColorPrint.RED}✗ {message}{ColorPrint.ENDC}")


def get_system_info():
    system = platform.system().lower()
    machine = platform.machine().lower()
    return system, machine


def run_command(cmd, cwd=None, ignore_errors=False):
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Print output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # Get the return code
        return_code = process.poll()

        if return_code != 0 and not ignore_errors:
            error_output = process.stderr.read()
            raise subprocess.CalledProcessError(return_code, cmd, error_output)

        return return_code

    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            ColorPrint.print_error(f"Error executing command: {cmd}")
            ColorPrint.print_error(f"Error output: {e.output}")
            raise
        return e.returncode


def install_dependencies():
    system, _ = get_system_info()

    ColorPrint.print_step(1, 4, "Installing dependencies...")

    if system == "linux":
        run_command("sudo apt-get update")
        run_command("sudo apt-get install -y cmake build-essential git python3-pip")
    elif system == "darwin":
        run_command("brew install cmake git")
    elif system == "windows":
        run_command("choco install cmake git python")

    ColorPrint.print_success("Dependencies installed successfully")


def download_and_build_csmith():
    ColorPrint.print_step(2, 4, "Downloading and building Csmith...")

    if os.path.exists("csmith"):
        shutil.rmtree("csmith")

    print("Cloning Csmith repository...")
    run_command("git clone https://github.com/csmith-project/csmith.git")

    os.makedirs("csmith/build", exist_ok=True)

    print("Building Csmith...")
    system, _ = get_system_info()

    try:
        # Configure CMake with specific options
        cmake_configure_cmd = [
            "cmake ..",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DENABLE_TESTING=OFF"
        ]

        if system == "darwin":
            # Add macOS specific flags if needed
            cmake_configure_cmd.extend([
                "-DCMAKE_C_FLAGS='-Wno-error'",
                "-DCMAKE_CXX_FLAGS='-Wno-error'"
            ])

        run_command(" ".join(cmake_configure_cmd), cwd="csmith/build")

        # Build with multiple attempts and different targets
        build_targets = ["libcsmith_a", "libcsmith_so", "csmith"]
        for target in build_targets:
            try:
                print(f"Building target: {target}")
                run_command(f"cmake --build . --target {target}", cwd="csmith/build")
            except subprocess.CalledProcessError as e:
                ColorPrint.print_error(f"Failed to build target {target}, continuing with next target...")
                continue

        # Verify the essential binaries exist
        csmith_binary = "csmith/build/src/csmith"
        if system == "windows":
            csmith_binary += ".exe"

        if not os.path.exists(csmith_binary):
            raise Exception("Csmith binary was not built successfully")

        ColorPrint.print_success("Csmith built successfully")

    except Exception as e:
        ColorPrint.print_error(f"Error building Csmith: {str(e)}")
        ColorPrint.print_error("Attempting alternative build method...")

        # Alternative build method
        try:
            run_command("cmake -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTING=OFF ..", cwd="csmith/build")
            run_command("make -j$(nproc)", cwd="csmith/build", ignore_errors=True)

            if not os.path.exists(csmith_binary):
                raise Exception("Alternative build method also failed")

            ColorPrint.print_success("Csmith built successfully using alternative method")

        except Exception as e2:
            ColorPrint.print_error(f"Alternative build method also failed: {str(e2)}")
            raise Exception("Could not build Csmith")


def download_and_build_yarpgen():
    ColorPrint.print_step(3, 4, "Downloading and building YARPGEN...")

    if os.path.exists("yarpgen"):
        shutil.rmtree("yarpgen")

    print("Cloning YARPGEN repository...")
    run_command("git clone https://github.com/intel/yarpgen.git")

    os.makedirs("yarpgen/build", exist_ok=True)

    print("Building YARPGEN...")
    run_command("cmake ..", cwd="yarpgen/build")
    run_command("cmake --build .", cwd="yarpgen/build")

    ColorPrint.print_success("YARPGEN built successfully")


def download_with_progress(url, filename):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    with open(filename, 'wb') as f:
        with tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
                desc=f"Downloading {filename}"
        ) as pbar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                pbar.update(size)


def download_llvm():
    ColorPrint.print_step(4, 4, "Downloading LLVM...")
    system, machine = get_system_info()

    # LLVM 16.0.0 download URLs for different systems
    llvm_urls = {
        ("linux",
         "x86_64"): "https://github.com/llvm/llvm-project/releases/download/llvmorg-16.0.0/clang+llvm-16.0.0-x86_64-linux-gnu-ubuntu-18.04.tar.xz",
        ("darwin",
         "x86_64"): "https://github.com/llvm/llvm-project/releases/download/llvmorg-16.0.0/clang+llvm-16.0.0-x86_64-apple-darwin.tar.xz",
        ("darwin",
         "arm64"): "https://github.com/llvm/llvm-project/releases/download/llvmorg-16.0.0/clang+llvm-16.0.0-arm64-apple-darwin21.0.tar.xz",
        ("windows",
         "x86_64"): "https://github.com/llvm/llvm-project/releases/download/llvmorg-16.0.0/LLVM-16.0.0-win64.exe"
    }

    system_key = (system, machine)
    if system_key not in llvm_urls:
        ColorPrint.print_error(f"No pre-built LLVM binaries available for {system} {machine}")
        return

    url = llvm_urls[system_key]
    filename = url.split('/')[-1]

    # Download LLVM with progress bar
    download_with_progress(url, filename)

    print("Extracting/Installing LLVM...")
    # Extract or install LLVM
    if system == "windows":
        run_command(filename + " /S")
    else:
        with tarfile.open(filename) as tar:
            total_members = len(tar.getmembers())
            with tqdm(total=total_members, desc="Extracting LLVM") as pbar:
                for member in tar.getmembers():
                    tar.extract(member)
                    pbar.update(1)

    ColorPrint.print_success("LLVM downloaded and installed successfully")


def main():
    try:
        print(f"{ColorPrint.HEADER}{ColorPrint.BOLD}Starting installation process...{ColorPrint.ENDC}")

        # Get system information
        system, machine = get_system_info()
        print(f"\nDetected system: {system} {machine}")

        # Show total steps
        print(f"\nTotal steps to complete: 4")
        print("1. Install dependencies")
        print("2. Download and build Csmith")
        print("3. Download and build YARPGEN")
        print("4. Download and install LLVM")
        print("\nStarting installation...\n")

        # Install necessary dependencies
        install_dependencies()

        # Download and build tools
        download_and_build_csmith()
        download_and_build_yarpgen()
        download_llvm()

        print(
            f"\n{ColorPrint.GREEN}{ColorPrint.BOLD}All tools have been downloaded and built successfully!{ColorPrint.ENDC}")

    except Exception as e:
        ColorPrint.print_error(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
