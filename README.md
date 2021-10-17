# No Time To Flake
A tool to help developers find time-related flaky tests by utilizing the [faketime](https://github.com/wolfcw/libfaketime) library and TZ environment variable.  

## Dependencies
* Python3.6+
* Docker

## Installation
Once the dependencies are fulfilled, simply run:
```
pip install -r requirements.txt
```
to install required packages.

## Usage
### test-manager.py
```
usage: test-manager.py [-h] [-i IMAGE] [-d DEPENDENCY] project command

Run command at different time and in different timezone.

positional arguments:
  project               the GitHub project URL
  command               the command to run the test

optional arguments:
  -h, --help            show this help message and exit
  -i IMAGE, --image IMAGE
                        the Docker image URL
  -d DEPENDENCY, --dependency DEPENDENCY
                        the path to the files that contains the commands necessary to install all
                        dependencies and the project
```
<br/><br/>
Additionally, test.runner.py can be use as a stand-alone tool to run a command with faked time and/or timezone.
### test-runner.py
faketime string's format can be found in faketime's GitHub repo.
```
usage: test-runner.py [-h] -f FAKETIME [-p PRELOAD] [-tz TIMEZONE] command

Run command at different time and in different timezone.

positional arguments:
  command               the arguments used to launch the test cases

optional arguments:
  -h, --help            show this help message and exit
  -f FAKETIME, --faketime FAKETIME
                        the faketime string
  -p PRELOAD, --preload PRELOAD
                        path to the faketime preload library
  -tz TIMEZONE, --timezone TIMEZONE
                        timezone to run the command inn
```
## Example usage
### test-manager.py
Current test-manager.py only run whatever command that the user provide without faking neither time nor timezone. But you can still try to use it:
```
python3 test-manager.py https://github.com/alibaba/Sentinel "mvn -fae test" -i maven:3.8.3-jdk-8-openj9
```
This will create a Docker container using the "maven:3.8.3-jdk-8-openj9" image and install libfaketime with all the other dependencies automatically. And then, it will run the test-runner.py on "Sentinel" project with the common "mvn -fae test" without faking time or timezone.

### test-runner.py
There are two obvious time-related flaky in [fake-test.py](https://github.com/polohan/CS-527-Project/blob/master/utility/fake-test.py) tests that could fail under very rare conditions.  
Try to run the test using:  
```
python3 fake-test.py
```
The two tests should pass without any problem.
Now try to run the test using the tool that will speed up the clock speed by 10000 times:
```
python3 test-runner.py -f '+0 x10000' 'python3 ./utility/fake-test.py'
```
This will make the runtime for the system calls that retrieve the current time 10000 times longer, which makes them likely to cross the second boundary and cause the test cases to fail.
