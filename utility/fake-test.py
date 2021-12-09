from datetime import datetime
from time import sleep, time
import unittest

class TestStringMethods(unittest.TestCase):

    def test_same_second(self):
        # strftime(): return a string representing the date,
        # controlled by an explicit format string
        time_0 = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        time_1 = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.assertEqual(time_0, time_1)

    def test_plus_one_second(self):
        # time(): return the time in seconds since the epoch
        # as a floating point number 
        time_0 = int(time())
        sleep(1)
        time_1 = int(time())
        self.assertEqual(time_0 + 1, time_1)

    def test_same_minute(self):
        time_0 = datetime.now().strftime("%Y-%m-%dT%H:%M")
        time_1 = datetime.now().strftime("%Y-%m-%dT%H:%M")
        self.assertEqual(time_0, time_1)
    
    def test_same_month(self):
        time_0 = datetime.now().strftime("%Y-%m")
        time_1 = datetime.now().strftime("%Y-%m")
        self.assertEqual(time_0, time_1)

    def test_same_year(self):
        time_0 = datetime.now().strftime("%Y")
        time_1 = datetime.now().strftime("%Y")
        self.assertEqual(time_0, time_1)

if __name__ == '__main__':
    unittest.main()