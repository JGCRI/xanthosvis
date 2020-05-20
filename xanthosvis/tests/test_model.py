"""Tests for the main functionality.

:author:   Chris R. Vernon
:email:    chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import unittest

import xanthosvis.main as tester


class TestModel(unittest.TestCase):
    """Tests for the `ReadConfig` class that reads the input configuration from the user."""

    def test_model_outputs(self):
        """Ensure model outputs are what is expected."""

        self.assertEqual(tester.dump_this(), 0)


if __name__ == '__main__':
    unittest.main()
