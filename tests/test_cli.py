import unittest
import subprocess
from pathlib import Path


root_path = src = Path(__file__).parent.parent
src = Path(__file__).parent.parent / 'src'
cli_path = src / 'cli.py'
sample_audio = root_path / 'sample-short.wav'


class TestAuth(unittest.TestCase):
    

    def test_render_via_cli(self):
        output_path = root_path / 'out/unittest.mp4'

        try:
            output_path.unlink()
        except FileNotFoundError:
            pass

        args = [
            cli_path.absolute(),
            '--audio', sample_audio.absolute(),
            '--output', output_path.absolute()
        ]

        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"CLI failed with error: {result.stderr}")

        self.assertTrue(output_path.exists())