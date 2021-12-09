"""
The test manager should:
1. Accepts Docker Image URL, Target Project URL, commands to install dependencies as input
2. Uses the above information to create a Docker container to run and monitor the test sequences
3. Generates the reports at the end
"""

import argparse
import os
import signal
import tarfile
from datetime import datetime
from io import FileIO, StringIO
from typing import List

import docker
from docker.models.containers import Container

SCRIPT_FOLDER = "bash"
BASIC_DEPENDENCY_INSTALLATION_SCRIPT = "install_basic_dependency.sh"
TEST_RUNNER_SCRIPT = "test-runner.py"
TEST_RUNNER_DEPENDENCY_FILE = "requirements.txt"
THIS_PROJECT_URL = "https://github.com/polohan/No-Time-To-Flake"
LIBFAKETIME_PROJECT_URL = "https://github.com/polohan/libfaketime"
THIS_PROJECT_FOLDER = "tool"
RUNNER_SCRIPT = "test-runner.py"
TARGET_PROJECT_FOLDER = "target"
LIBFAKETIME_FOLDER = "libfaketime"

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

def _get_container(container_id: str) -> Container:
    """Get the Docker container to run the test sequence in.

    Args:
        container_id (str): the container id

    Returns:
        container: a Docker container obj
    """
    client = docker.from_env()
    container = client.containers.get(container_id)
    return container

# Source: https://stackoverflow.com/a/52716666
def _copy_file(container: Container, src: str, dst: str) -> None:
    """Copy a file into container.

    Args:
        container (Container): the target container to copy the file into
        src (str): source path of the copied file
        dst (str): destination path of the copied file
    """
    cwd = os.getcwd()
    file_name = os.path.basename(src)
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

def _run_cmds(container: Container, commands: List[str], workdir: str = None, stream: bool = False, pipe: FileIO = None, force_stdout: bool = False) -> None:
    """Run a command inside the container.

    Args:
        container (Container): the container to run the commands in
        commands (List[str]): command to be executed
        workdir (str): the working directory to run the command on
        stream (bool): whether to stream the output
        pipe (FileIO, None): a file-like object to stream the output to. Default to None
        force_stdout (bool): whether to also print to stdout when pipe is not None.
    """
    exit_code, output = container.exec_run(commands, privileged=True, stream=stream, workdir=workdir)
    if not stream:
        if exit_code != 0:
            print(output.decode(), end="")
            raise Exception(f"exec_run exits with non-zero exit code: {exit_code}")
    else:
        for data in output:
            try:
                decoded_data = data.decode()
            except UnicodeDecodeError:
                decoded_data = data
            if pipe:
                print(decoded_data, end="", file=pipe)
                if force_stdout:
                    print(decoded_data, end="")
            else:
                    print(decoded_data, end="")

def _install_faketime(container: Container, workdir: str = '/') -> None:
    """Install libfaketime in this container.
    If the 'make test' fail, add the CFLAG -DFORCE_MONOTONIC_FIX to
    src/Makefile.

    Args:
        container (Container): the container to install the libfaketime on
        workdir (str): the working directory to use when installing libfaketime
    """
    # download and unzip library
    dependency_cmd = ["git", "clone", LIBFAKETIME_PROJECT_URL, LIBFAKETIME_FOLDER]
    _run_cmds(container, dependency_cmd, workdir)

    # run make test and wait to see if it hangs
    def _handler(signum, frame):
        print('Faketime hangs when runnning make test.')
        raise TimeoutError('Faketime hangs when runnning make test.')

    # set the timeout handler
    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(60)    # wait 60 sec

    fake_file = StringIO()
    libfaketime_path = os.path.join(workdir, LIBFAKETIME_FOLDER)
    
    try:
        _run_cmds(container, ['make', 'test'], libfaketime_path, True, fake_file)
    except TimeoutError:
        output_lines = fake_file.getvalue().splitlines()
        if "CLOCK_MONOTONIC" in output_lines[-1]:
            print('"CLOCK_MONOTONIC test" apparently hang forever.')
            print('Adding additional DFORCE_MONOTONIC_FIX CFLAG.')
            _run_cmds(container, ['sed', '-i', '84 i CFLAGS += -DFORCE_MONOTONIC_FIX', './src/Makefile'],
                libfaketime_path)
        else:
            print(output_lines)
            raise TimeoutError("Faketime hangs when running make test with unknown cause.")
    finally:
        _run_cmds(container, ['make', 'clean'], libfaketime_path)
        signal.alarm(0) # cancel alarm

    # install libfaketime
    print("Performing make install.")
    _run_cmds(container, ['make', 'install'], libfaketime_path)

def prepare_container(image_url: str, dependency_file: str, target_project_url: str, project_folder: str = '/home', container_id: str = '') -> None:
    """Create the container for the test sequence.

    Args:
        image_url (str): the image to run
        dependency_file (str): the path to the dependency file
        target_project_url (str): the project to test
        project_folder (str): the folder to put the project in
        container_id (str): the id of the container to run the test in. Defaults to ''.
    """
    if not container_id:
        # create container
        print("Creating container.")
        container = _create_container(image_url)
        print("Container created.")
    else:
        # get container
        print("Getting container.")
        container = _get_container(container_id)
        return container

    # install basic dependencies
    print("Installing basic dependencies.")
    file_name = BASIC_DEPENDENCY_INSTALLATION_SCRIPT
    file_path = os.path.join(SCRIPT_FOLDER, file_name)
    _copy_file(container, file_path, '/')
    dependency_cmd = ["bash", "-e", file_name, '/']
    _run_cmds(container, dependency_cmd)
    print("Basic dependencies installed.")

    # install libfaketime
    print("Installing libfaketime.")
    _install_faketime(container)
    print("libfaketime installed.")

    # copy other necessary file
    this_project_path_in_container = os.path.join(project_folder, THIS_PROJECT_FOLDER)
    _run_cmds(container, ["mkdir", THIS_PROJECT_FOLDER], project_folder)

    file_name = TEST_RUNNER_SCRIPT
    file_path = os.path.join('./', file_name)
    _copy_file(container, file_path, this_project_path_in_container)

    file_name = TEST_RUNNER_DEPENDENCY_FILE
    file_path = os.path.join('./', file_name)
    _copy_file(container, file_path, this_project_path_in_container)
    _run_cmds(container, ["pip", "install", "-r", "requirements.txt"], this_project_path_in_container)

    # download project
    print("Downloading projects from GitHub.")
    _run_cmds(container, ["git", "clone", target_project_url, TARGET_PROJECT_FOLDER], project_folder)
    print("Projects downloaded.")

    # run dependency_file if exist
    if dependency_file and os.path.isfile(dependency_file):
        print("Running dependency script.")
        dependency_file = os.path.abspath(dependency_file)
        file_name = os.path.basename(dependency_file)
        project_path = os.path.join(project_folder, TARGET_PROJECT_FOLDER)
        
        _copy_file(container, dependency_file, project_path)

        # run the file to install additional dependency and install the project (if necessary)
        dependency_cmd = ["bash", "-e", file_name]
        _run_cmds(container, dependency_cmd, project_path, stream=True)
        print("Dependency script finished with no error.")
    
    return container

def run_test(container: Container, command: str, faketime: str = '', timezone: str = '', project_folder: str = '/home', output_file: str = '', overwrite: bool = False) -> None:
    """Run a single test run in the container.

    Args:
        container (Container): the target container to run the test in
        command (str): the command to start the test for target project
        faketime (str, optional): the faketime format string. Defaults to '' if using actual time.
        switch (str, optional): the signifier in test output to reset the time. Defaults to None.
        timezone (str, optional): the TZ timezone string. Defaults to '' if using actual timezone.
        project_folder (str, optional): the folder that contains the target project and tool. Defaults to '/home'.
        output_file (str, optional): the path of the file to write the output to.
        overwrite (bool): whether to replace the old run result if old one already exist. Default to false.
    """
    target_project_path = os.path.join(project_folder, TARGET_PROJECT_FOLDER)

    write_pipe = None
    if output_file:
        if os.path.exists(output_file) and not overwrite:
            print(f"{output_file} already exists. Skipping test.")
            return
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        write_pipe = open(output_file, 'w', encoding="utf-8")

    _run_cmds(container, ['python3',
                            os.path.join('../', THIS_PROJECT_FOLDER, RUNNER_SCRIPT),
                            '-f', faketime,
                            '-tz', timezone
                        ] + [command], target_project_path, True, pipe=write_pipe, force_stdout=True)

def start(image_url: str, dependency_file: str, target_project_url: str, command: str, output_path: str, container_id: str = '') -> None:
    """Start the whole test process

    Args:
        image_url (str): the image to run
        dependency_file (str): the path to the dependency file
        target_project_url (str): the project to test
        command (str): the command to run the project
        output_path (str): the dir to put the output files in
        container_id (str): the id of the container to run the test in. Defaults to ''.
    """
    if target_project_url[-1] == '/':
        target_project_url = target_project_url[:-1]

    container = prepare_container(image_url, dependency_file, target_project_url, container_id=container_id)
    target_project_name = target_project_url.split('/')[-1]

    # dry run
    run_test(container, command)
    # singly run it without faking time/timezone
    run_test(container, command, output_file=os.path.join(output_path, target_project_name, 'test-ori.out'))
    # run with faketime but don't actual fake anything
    run_test(container, command, output_file=os.path.join(output_path, target_project_name, 'test-fake-ref.out'), faketime='+0')
    # run with faketime with speed up but don't actually speed up
    run_test(container, command, output_file=os.path.join(output_path, target_project_name, 'test-fake-speed-up-ref.out'), faketime='+0 x1.0')
    # run with faketime with adv increment feature
    run_test(container, command, output_file=os.path.join(output_path, target_project_name, 'test-fake-inc-ref.out'), faketime='+0 i1.0')

    # test with different potentially buggy timezones
    curr_year = datetime.now().year
    mock_timezones = [
        ("", "UTC", "UTC-ref"),
        ("", "Asia/Kolkata", None),     # UTC+5:30
        ("", "Australia/Eucla", None),      # UTC+8:45
        ("", "Pacific/Marquesas", None),      # UTC-9:30
        (f"@{curr_year}-07-01 00:00:00", "Pacific/Chatham", "Chatham"),      # UTC+12:45
        (f"@{curr_year}-01-01 00:00:00", "Pacific/Chatham", "Chatham-DST"),      # UTC+13:45
    ]
    for fake_time, fake_time_zone, name in mock_timezones:
        if not name:
            name = fake_time_zone if '/' not in fake_time_zone else fake_time_zone.split('/')[-1]
        
        run_test(container, command, output_file=os.path.join(output_path, target_project_name, f'test-fake-timezone-{name}.out'), faketime=fake_time, timezone=fake_time_zone)

    run_test(container, command, output_file=os.path.join(output_path, target_project_name, 'test-fake-ref.out'), faketime='+0')

    # speed up runs
    speed_up_factors = [2, 1000, 10000]
    for factor in speed_up_factors:
        run_test(container, command, output_file=os.path.join(output_path, target_project_name, f'test-fake-speed-up-{factor}x.out'), faketime=f'+0 x{factor}.0')

    # advanced increment runs
    increment_factors = [2]
    for factor in increment_factors:
        run_test(container, command, output_file=os.path.join(output_path, target_project_name, f'test-fake-inc-{factor}i.out'), faketime=f'+0 i{factor}.0')

    # switching runs
    for gap in range(1, 21):
        run_test(container, command, output_file=os.path.join(output_path, target_project_name, f'test-switch-{gap}.out'), faketime=f's {gap}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run command at different time and in different timezone.')
    parser.add_argument("-i", "--image", type=str, help="the Docker image URL", default="ubuntu:20.04")
    parser.add_argument("-d", "--dependency", type=str,
        help="the path to the files that contains the commands necessary to install all dependencies and the project")
    parser.add_argument("-p", "--path", type=str, help='the folder to put the output file in', default='./output')
    parser.add_argument("--id", type=str, help="the Docker container ID to run in")
    parser.add_argument("project", type=str, help="the GitHub project URL")
    parser.add_argument("command", type=str, help="the command to run the test")

    args = parser.parse_args()
    start(args.image, args.dependency, args.project, args.command, args.path, args.id)
