import unittest
import sys
sys.path.insert(0, '../')

from mp3_duration import mp3_duration

class Mp3DurationMethods(unittest.TestCase):

    def test_cbr(self):
        self.assertEqual(mp3_duration('demo - cbr.mp3'), 285.78)

    def test_cbr_estimate(self):
        self.assertEqual(mp3_duration('demo - cbr.mp3', True), 285.727)

    def test_vbr(self):
        self.assertEqual(mp3_duration('demo - vbr.mp3'), 285.727)

if __name__ == '__main__':
    unittest.main()