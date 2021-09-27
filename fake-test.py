from datetime import datetime
from time import sleep, time
import unittest

class TestStringMethods(unittest.TestCase):

    def test_same_second(self):
        time_0 = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S %Z")
        time_1 = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S %Z")
        self.assertEqual(time_0, time_1)

    def test_plus_one_second(self):
        time_0 = int(time())
        sleep(1)
        time_1 = int(time())
        self.assertEqual(time_0 + 1, time_1)

if __name__ == '__main__':
    unittest.main()