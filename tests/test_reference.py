"""Tests for included reference files and variables.

:author:   Jason Evanoff
:email:    jason.evanoff@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import pkg_resources
import tempfile
import unittest


class TestReferences(unittest.TestCase):
    """Tests for the `ReadConfig` class that reads the input configuration from the user."""

    # test config YAML file
    CONFIG_YAML = pkg_resources.resource_filename('im3py', 'tests/data/inputs/config.yml')

    # existing directory
    REAL_DIRPATH = pkg_resources.resource_filename('im3py', 'tests/data')

    # expected attribute values
    START_STEP = 2015
    THROUGH_STEP = 2016
    TIME_STEP = 1
    ALPHA_PARAM = 2.0
    BETA_PARAM = 1.42

    # expected attribute types
    START_STEP_TYPE = int
    THROUGH_STEP_TYPE = int
    TIME_STEP_TYPE = int
    ALPHA_PARAM_TYPE = float
    BETA_PARAM_TYPE = float

    def test_instance_attributes_config(self):
        """Test that the correct instance attribute values are generated from the config file read."""

        # read configuration from file
        cfg = ReadConfig(config_file=TestReadConfig.CONFIG_YAML)
        cfg.output_directory = TestReadConfig.REAL_DIRPATH

        # check value equality for each variable with expected
        self.check_values(cfg)

        # check type equality for each variable with expected
        self.check_types(cfg)

    def test_instance_attributes_params(self):
        """Test that the correct instance attribute values are generated from parameters."""

        # create a temporary directory to hold the outputs
        with tempfile.TemporaryDirectory() as dirpath:
            # read configuration from parameters
            cfg = ReadConfig(output_directory=dirpath,
                             start_step=TestReadConfig.START_STEP,
                             through_step=TestReadConfig.THROUGH_STEP,
                             time_step=TestReadConfig.TIME_STEP,
                             alpha_param=TestReadConfig.ALPHA_PARAM,
                             beta_param=TestReadConfig.BETA_PARAM,
                             write_logfile=False)

            # check value equality for each variable with expected
            self.check_values(cfg)

            # check type equality for each variable with expected
            self.check_types(cfg)

    def check_values(self, cfg):
        """Check values of each configuration attribute against expected.

        :param cfg:                     Configuration object

        """

        self.assertEqual(cfg.start_step, TestReadConfig.START_STEP)
        self.assertEqual(cfg.through_step, TestReadConfig.THROUGH_STEP)
        self.assertEqual(cfg.time_step, TestReadConfig.TIME_STEP)
        self.assertEqual(cfg.alpha_param, TestReadConfig.ALPHA_PARAM)
        self.assertEqual(cfg.beta_param, TestReadConfig.BETA_PARAM)

    def check_types(self, cfg):
        """Check types of each configuration attribute against expected.

        :param cfg:                     Configuration object

        """

        self.assertEqual(type(cfg.start_step), TestReadConfig.START_STEP_TYPE)
        self.assertEqual(type(cfg.through_step), TestReadConfig.THROUGH_STEP_TYPE)
        self.assertEqual(type(cfg.time_step), TestReadConfig.TIME_STEP_TYPE)
        self.assertEqual(type(cfg.alpha_param), TestReadConfig.ALPHA_PARAM_TYPE)
        self.assertEqual(type(cfg.beta_param), TestReadConfig.BETA_PARAM_TYPE)


if __name__ == '__main__':
    unittest.main()