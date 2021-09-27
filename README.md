# CS-527-Project
A tool to help developer find time-realted flaky test that utilize the [faketime](https://github.com/wolfcw/libfaketime) library.

## Usage
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
In [fake-test.py](https://github.com/polohan/CS-527-Project/blob/master/fake-test.py), there are two obvious time-related flaky test that could failed under very rare condition.  
Try to run the test using:  
```console
python3 fake-test.py
```
The two tests should passed without problem.
Now try to run the test using the tool that will speed up the clock speed by 10000 times:
```console
python3 test-manager.py -f '+0 x10000' python3 fake-test.py
```
This will make the runtime for the system calls that retrieve the current time 10000 times longer, which makes them likely to cross the second boundary and causing the test cases to fail.
