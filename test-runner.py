import argparse
import os
import random
import subprocess
from datetime import datetime

LOG_FILE_DIR = './output'
LD_PRELOAD_VAL = '/usr/local/lib/faketime/libfaketime.so.1'

def _set_faketime(faketime):
    with open(os.path.expanduser('~/.faketimerc'), 'w') as f:
        f.write(faketime)
        f.close()

def _test_runner_simple(command, faketime, timezone, output_file_name):
    # TODO: implement switcher to switch between two faketime while running tests
    test_env = os.environ.copy()
    test_env["LD_PRELOAD"] = LD_PRELOAD_VAL
    test_env["FAKETIME"] = faketime
    if timezone: test_env["TZ"] = timezone

    os.makedirs(LOG_FILE_DIR, exist_ok=True)
    with open(os.path.join(LOG_FILE_DIR, output_file_name), 'w') as f, subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=test_env) as process:
        while process.poll() is None:
            line = process.stdout.readline()
            print(line, end='')
            print(line, end='', file=f)
        f.close()
    
    return process.poll() != 0  # if test failed

def _test_runner_switch(command, switch, timezone, output_file_name):
    # TODO: use _set_faketime to change the faketime string dynamically
    pass

def _run_test_once(command, faketime='', switch=None, timezone=''):
    curr_time_str = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S")
    command = command.split()
    ret = {
        "error": False,
        "log_file": f"output-{curr_time_str}-{str(random.randint(0, 9999)).zfill(4)}.log",
        "message": '',
        "start_time": curr_time_str,
        "end_time": None,
        "command": command,
        "faketime_str": faketime,
        "timezone": timezone if timezone else datetime.now().astimezone().tzinfo
    }

    if not switch:
        ret["error"] = _test_runner_simple(command, faketime, timezone, ret['log_file'])
    else:
        ret["error"] = _test_runner_switch(command, switch, timezone, ret['log_file'])

    ret["end_time"] = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S")
    return ret

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run command at different time and in different timezone.')
    parser.add_argument("-f", "--faketime", type=str, help="the faketime string", required=True)
    parser.add_argument("-p", "--preload", type=str, help="path to the faketime preload library")
    parser.add_argument("-tz", "--timezone", type=str, help="timezone to run the command in")
    parser.add_argument("command", type=str, help='the arguments used to launch the test cases')
    args = parser.parse_args()

    if args.preload:
        LD_PRELOAD_VAL = args.preload

    # TODO: build complete test sequence instead of hardcode faketime
    res = _run_test_once(args.command, args.faketime, timezone=args.timezone)
    print(res)
