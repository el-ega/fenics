import subprocess

from django.test import TestCase


PACKAGES = ['ega', 'fenics']


class Flake8ConformanceTestCase(TestCase):
    excludes = ['ega/migrations']

    def test_lint(self):
        excludes = ','.join(self.excludes)
        cmd = ['flake8', '--exclude', excludes] + PACKAGES
        try:
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print('\n\n\n', ' '.join(cmd))
            result = e.stdout.decode('utf-8')
            # If at least one error is found, the exception is raised. We
            # prepend a '\n' so 'AssertionError is on a line by itself.
            self.assertEqual('', result, '\n' + result)
