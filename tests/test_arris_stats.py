import os
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


if __name__ == '__main__':
    unittest.main()
