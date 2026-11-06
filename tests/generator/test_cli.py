import subprocess
import sys
import unittest


class CliTest(unittest.TestCase):
    def test_help_lists_commands(self):
        out = subprocess.run([sys.executable, "-m", "generator", "--help"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("fetch", out.stdout)

    def test_unknown_command_fails(self):
        out = subprocess.run([sys.executable, "-m", "generator", "nope"], capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)


if __name__ == "__main__":
    unittest.main()
