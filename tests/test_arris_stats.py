import os
import re
import unittest
import tempfile
import arris_stats


class TestArrisStats(unittest.TestCase):

    # Required params and their defaults that we need to get from the config file or ENV
    default_config = {

        # Main
        'destination': 'influxdb',
        'sleep_interval': 300,
        'modem_url': 'https://192.168.100.1/cmconnectionstatus.html',
        'modem_verify_ssl': False,
        'modem_auth_required': False,
        'modem_username': 'admin',
        'modem_password': None,
        'modem_model': 'sb8200',
        'exit_on_auth_error': True,
        'exit_on_html_error': True,
        'clear_auth_token_on_html_error': True,
        'sleep_before_exit': True,

        # Influx
        'influx_host': 'localhost',
        'influx_port': 8086,
        'influx_database': 'cable_modem_stats',
        'influx_username': None,
        'influx_password': None,
        'influx_use_ssl': False,
        'influx_verify_ssl': True,
    }

    def test_get_config(self):
        """ Test arris_stats.get_config() """
        default_config = self.default_config.copy()

        # Get the config without a config file or any ENV vars set, we should get the same dict as above
        config = arris_stats.get_config()
        for param in default_config:
            self.assertEqual(config[param], default_config[param])

        # Now test a config file
        default_config_dump = str(default_config)
        config_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        for param in default_config:
            line = "%s = %s\n" % (param, default_config[param])
            config_file.write(line)
        config_file.close()

        config = arris_stats.get_config(config_file.name)
        for param in default_config:
            self.assertEqual(config[param], default_config[param])

        # Set ENV values for each parameter
        for param in default_config:
            # For string params just set a value and see if we get it back
            if isinstance(default_config, str):
                os.environ[param] = 'test_value'

            # For boolean params let's flip the value
            if isinstance(default_config, bool):
                os.environ[param] = not default_config[param]

        # See if what we got back matches
        config = arris_stats.get_config()
        for param in default_config:
            # For string params just set a value and see if we get it back
            if isinstance(default_config, str):
                self.assertIsInstance(config[param], str)
                self.assertEqual(config[param], 'test_value')

            # For boolean params let's flip the value
            if isinstance(default_config, bool):
                self.assertIsInstance(config[param], bool)
                self.assertEqual(config[param], not default_config[param])

        # Do it again but ensure we're overriding the config file with ENV vars
        config = arris_stats.get_config(config_file.name)
        for param in default_config:
            # For string params just set a value and see if we get it back
            if isinstance(default_config, str):
                self.assertIsInstance(config[param], str)
                self.assertEqual(config[param], 'test_value')

            # For boolean params let's flip the value
            if isinstance(default_config, bool):
                self.assertIsInstance(config[param], bool)
                self.assertEqual(config[param], not default_config[param])

    def test_dockerfile(self):
        """ Ensure the docker file has the same hard coded ENV defaults """
        default_config = self.default_config.copy()
        path = 'Dockerfile'
        with open(path, "r") as dockerfile:
            dockerfile_contents = dockerfile.read().splitlines()
        for line in dockerfile_contents:
            if re.match(r'^ENV \S+ \S+$', line):
                param = line.split(' ')[1]
                value = line.split(' ')[2]
                self.assertEqual(str(default_config[param]), value)  # Param is in Dockerfile but not default_config, or default values do not match
                del default_config[param]  # Delete it once found so we can identify missing params

        empty_dict = {}
        self.assertEqual(default_config, empty_dict)  # default_config should be empty, if not then the Dockerfile is missing params

    def test_config_file(self):
        """ Ensure the config file as the same hard coded defaults as default_config """

        default_config = self.default_config.copy()
        path = 'src/config.ini'
        with open(path, "r") as configfile:
            config_contents = configfile.read().splitlines()
        for line in config_contents:
            param = line.split(' = ')[0]
            value = line.split(' = ')[1]
            self.assertEqual(str(default_config[param]), value)  # Param is in config file but not default_config, or default values do not match
            del default_config[param]  # Delete it once found so we can identify missing params

        empty_dict = {}
        self.assertEqual(default_config, empty_dict)  # default_config should be empty, if not then the Dockerfile is missing params


if __name__ == '__main__':
    unittest.main()
