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

def _create_container(image_url: str) -> Container:
    """Create the Docker container to run the test sequence in.

    Args:
        image_url (str): the image to run

    Returns:
        container: a Docker container obj
    """
    client = docker.from_env()
    container = client.containers.run(image_url, tty=True, detach=True)
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
    _, stream = container.exec_run(commands, privileged=True, stream=True, workdir=workdir)
    for data in stream:
        print(data.decode(), end="")

def _prepare_container(image_url: str, dependency_file: str, github_url: str) -> None:
    """Create the container for the test sequence.

    Args:
        image_url (str): the image to run
        dependency_file (str): the path to the dependency file
        github_url (str): the project to test
    """
    # create container
    container = _create_container(image_url)

    # copy dependency_file to container if exist
    if dependency_file and os.path.isfile(dependency_file):
        file_name = os.path.basename(dependency_file)
        
        _copy_file(container, file_name, dependency_file, '/')

        # run the file to install dependency
        dependency_cmd = ["bash", file_name, '/']
        _run_cmds(container, dependency_cmd)

    # install git and libfaketime
    file_name = BASIC_DEPENDENCY_INSTALLATION_FILE
    _copy_file(container, file_name, file_name, '/')
    dependency_cmd = ["bash", file_name, '/']
    _run_cmds(container, dependency_cmd)
    
    # install project
    _run_cmds(container, ["git", "clone", github_url], '/home')
    
    return container

def start(image_url: str, dependency_file: str, github_url: str, command: str) -> None:
    """Start the whole test process

    Args:
        image_url (str): the image to run
        dependency_file (str): the path to the dependency file
        github_url (str): the project to test
        command (str): the command to run the project
    """
    container = _prepare_container(image_url, dependency_file, github_url)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run command at different time and in different timezone.')
    parser.add_argument("-i", "--image", type=str, help="the Docker image URL", default="ubuntu:20.04")
    parser.add_argument("-d", "--dependency", type=str,
        help="the path to the files that contains the command to install all dependencies")
    parser.add_argument("-p", "--project", type=str, help="the GitHub project URL", required=True)
    parser.add_argument("-c", "--command", type=str, help="the command to run the test sequence on", required=True)

    args = parser.parse_args()
    start(args.image, args.dependency, args.project, args.command)
