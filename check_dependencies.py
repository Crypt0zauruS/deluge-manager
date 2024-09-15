import pkg_resources # type: ignore
import subprocess
import sys

def install_missing(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_dependencies():
    with open("requirements.txt", "r") as req_file:
        requirements = req_file.readlines()

    for requirement in requirements:
        requirement = requirement.strip()
        if requirement and not requirement.startswith("#"):
            try:
                pkg_resources.require(requirement)
            except pkg_resources.DistributionNotFound:
                print(f"{requirement} not installed. Installing...")
                install_missing(requirement)
            except pkg_resources.VersionConflict as e:
                print(f"Version conflict for {requirement}: {e}. Installing correct version...")
                install_missing(requirement)

if __name__ == "__main__":
    check_dependencies()
