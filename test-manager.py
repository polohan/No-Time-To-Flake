"""
The test manager that should:
1. Accepts Docker Image URL, Target Project URL, commands to install dependencies as input
2. Uses the above information to create a Docker container to run and monitor the test sequences
3. Generates the reports at the end
"""

import argparse
import os
import tarfile
from typing import List

import docker
from docker.models.containers import Container

BASIC_DEPENDENCY_INSTALLATION_FILE = "./install_basic_dependency.sh"
THIS_PROJECT_URL = "https://github.com/polohan/CS-527-Project"

def _create_container(image_url: str) -> Container:
    """Create the Docker container to run the test sequence in.

    Args:
        image_url (str): the image to run

    Returns:
        container: a Docker container obj
    """
    client = docker.from_env()
    container = client.containers.run(image_url, 'bash', tty=True, detach=True)
    return container

# Source: https://stackoverflow.com/a/52716666
def _copy_file(container: Container, file_name: str, src: str, dst: str) -> None:
    """Copy a file into container.

    Args:
        container (Container): the target container to copy the file into
        file_name (str): the file name of the copied file
        src (str): source path of the copied file
        dst (str): destination path of the copied file
    """
    cwd = os.getcwd()
    os.chdir(os.path.dirname(src))
    tmp_tar_name = f'{file_name}.tar'
    tmp_tar = tarfile.open(tmp_tar_name, mode='w')

    try:
        tmp_tar.add(file_name)
    finally:
        tmp_tar.close()

    data = open(tmp_tar_name, 'rb').read()
    container.put_archive(dst, data)
    os.remove(tmp_tar_name)
    os.chdir(cwd)

def _run_cmds(container: Container, commands: List[str], workdir: str = None) -> None:
    """Run a command inside the container.

    Args:
        container (Container): the container to run the commands in
        commands (List[str]): command to be executed
        workdir (str): the working directory to run the command on
    """
    exit_code, output = container.exec_run(commands, privileged=True, stream=False, workdir=workdir)
    if exit_code != 0:
        print(output.decode(), end="")
        raise Exception(f"exec_run exits with non-zero exit code: {exit_code}")
        

def _prepare_container(image_url: str, dependency_file: str, target_project_url: str) -> None:
    """Create the container for the test sequence.

    Args:
        image_url (str): the image to run
        dependency_file (str): the path to the dependency file
        target_project_url (str): the project to test
    """
    # create container
    print("Creating container.")
    container = _create_container(image_url)
    print("Container created.")

    # install git and libfaketime
    print("Installing Git, libfaketime and Python3.")
    file_name = BASIC_DEPENDENCY_INSTALLATION_FILE
    _copy_file(container, file_name, file_name, '/')
    dependency_cmd = ["bash", "-e", file_name, '/']
    _run_cmds(container, dependency_cmd)
    print("Git, libfaketime and Python3 installed.")
    
    # download projects
    print("Downloading projects from GitHub.")
    _run_cmds(container, ["git", "clone", THIS_PROJECT_URL], '/home')
    _run_cmds(container, ["git", "clone", target_project_url], '/home')
    print("Projects downloaded.")

    # copy dependency_file to container if exist
    if dependency_file and os.path.isfile(dependency_file):
        print("Running dependency script.")
        dependency_file = os.path.abspath(dependency_file)
        file_name = os.path.basename(dependency_file)
        project_name = target_project_url.split('/')[-1]
        project_path = os.path.join('/home', project_name)
        
        _copy_file(container, file_name, dependency_file, project_path)

        # run the file to install additional dependency and install the project (if necessary)
        dependency_cmd = ["bash", "-e", file_name]
        _run_cmds(container, dependency_cmd, project_path)
        print("Dependency script finished with no error.")
    
    return container

def start(image_url: str, dependency_file: str, target_project_url: str, command: str) -> None:
    """Start the whole test process

    Args:
        image_url (str): the image to run
        dependency_file (str): the path to the dependency file
        target_project_url (str): the project to test
        command (str): the command to run the project
    """
    container = _prepare_container(image_url, dependency_file, target_project_url)

    project_name = target_project_url.split('/')[-1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run command at different time and in different timezone.')
    parser.add_argument("-i", "--image", type=str, help="the Docker image URL", default="ubuntu:20.04")
    parser.add_argument("-d", "--dependency", type=str,
        help="the path to the files that contains the commands necessary to install all dependencies and the project")
    parser.add_argument("project", type=str, help="the GitHub project URL")
    parser.add_argument("command", type=str, help="the command to run the test")

    args = parser.parse_args()
    start(args.image, args.dependency, args.project, args.command)
