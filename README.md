# CS-527-Project
A tool to help developers find time-related flaky tests by utilizing the [faketime](https://github.com/wolfcw/libfaketime) library and TZ environment variable.

## Installation

An automated install tool is coming soon. But as of right now, you need to install the faketime tool yourself, and guidance can be found [here](https://github.com/wolfcw/libfaketime).

Once faketime is installed, you can install the Python dependencies using:
```console
pip install -r requirements.txt
```

## Usage
faketime string's format can be found in faketime's GitHub repo.
```
usage: test-manager.py [-h] -f FAKETIME [-p PRELOAD] [-tz TIMEZONE] args [args ...]

Find time-related flaky test.

positional arguments:
  args                  the arguments used to launch the test cases

optional arguments:
  -h, --help            show this help message and exit
  -f FAKETIME, --faketime FAKETIME
                        the faketime string
  -p PRELOAD, --preload PRELOAD
                        path to the faketime preload library
  -tz TIMEZONE, --timezone TIMEZONE
                        timezone to run the command in
```

## Example use case
There are two obvious time-related flaky in [fake-test.py](https://github.com/polohan/CS-527-Project/blob/master/fake-test.py) tests that could fail under very rare conditions.  
Try to run the test using:  
```console
python3 fake-test.py
```
The two tests should pass without any problem.
Now try to run the test using the tool that will speed up the clock speed by 10000 times:
```console
python3 test-manager.py -f '+0 x10000' python3 fake-test.py
```
This will make the runtime for the system calls that retrieve the current time 10000 times longer, which makes them likely to cross the second boundary and cause the test cases to fail.
