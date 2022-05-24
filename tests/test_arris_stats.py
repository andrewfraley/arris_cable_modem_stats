import os
import re
import json
import unittest
import tempfile
import src.arris_stats as arris_stats

# pylint: disable=line-too-long


class TestArrisStats(unittest.TestCase):

    # Required params and their defaults that we need to get from the config file or ENV
    default_config = arris_stats.get_default_config()

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
        default_config = arris_stats.get_default_config().copy()
        path = 'Dockerfile'
        with open(path, "r") as dockerfile:
            dockerfile_contents = dockerfile.read().splitlines()

        # We need to search each line until we find the ENV line, then find the end of the list of ENV variables
        env_lines = []
        first = None
        for line in dockerfile_contents:

            # Find the first line
            if not first and re.match(r'^ENV \S+ \S+$', line):
                # ENV arris_stats_debug=False \
                first = line.split('ENV ')[1].split(' \\')[0].strip()
                env_lines.append(first)
            # Find the rest of the lines
            elif first:
                if re.match(r'\s*\S.+=\S.', line):
                    env_lines.append(line.split(' \\')[0].strip())
                # If the line isn't just whitespace or a comment, consider this the end of the ENV block
                elif line.strip() == '' or re.match(r'^#', line.strip()) or re.match(r'^\\', line.strip()):
                    continue
                else:
                    break
        # Now we have all the lines, test the values
        for line in env_lines:
            param = line.split('=')[0]
            value = line.split('=')[1]
            self.assertEqual(str(default_config[param]), value)  # Param is in Dockerfile but not default_config, or default values do not match
            del default_config[param]  # Delete it once found so we can identify missing params

        empty_dict = {}
        self.assertEqual(default_config, empty_dict)  # default_config should be empty, if not then the Dockerfile is missing params

    def test_config_file(self):
        """ Ensure the config file as the same hard coded defaults as default_config """

        default_config = self.default_config.copy()
        path = 'src/config.ini.example'
        with open(path, "r") as configfile:
            config_contents = configfile.read().splitlines()
        for line in config_contents:
            linesplit = line.split(' = ')
            if len(linesplit) != 2:
                continue
            param = linesplit[0]
            value = linesplit[1]
            self.assertEqual(str(default_config[param]), value)  # Param is in config file but not default_config, or default values do not match
            del default_config[param]  # Delete it once found so we can identify missing params

        empty_dict = {}
        self.assertEqual(default_config, empty_dict)  # default_config should be empty, if not then the Dockerfile is missing params

    def test_modem_parse_functions(self):
        """ Test all the modem parse functions """
        modems_supported = arris_stats.modems_supported

        for modem in modems_supported:

            # Get the control values
            with open('tests/mockups/%s.json' % modem) as f:
                control_values_string = f.read()
                control_values = json.loads(control_values_string)

            # Get the html
            with open('tests/mockups/%s.html' % modem) as f:
                html = f.read()

            # Get the proper function
            module = __import__('arris_stats_' + modem)
            parse_html_function = getattr(module, 'parse_html_' + modem)

            stats = parse_html_function(html)

            # Verify the correct types and root level indexes
            self.assertIsInstance(stats, dict)
            self.assertIn('downstream', stats)
            self.assertIn('upstream', stats)

            # Verify the values
            root_indexes = ['downstream', 'upstream']
            for root_index in root_indexes:
                for row in control_values[root_index]:
                    self.assertIn(row, stats[root_index])


if __name__ == '__main__':
    unittest.main()
