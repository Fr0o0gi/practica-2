import tempfile
import unittest
from pathlib import Path

from src.config import load_config


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "alpine.toml"


class ConfigTests(unittest.TestCase):
    """Проверяет конфигурацию и ошибки всех шести параметров."""

    def test_valid_file(self):
        """Читает действительную конфигурацию Alpine."""
        config = load_config(EXAMPLE)
        self.assertEqual(config.package, "curl")
        self.assertEqual(config.output.name, "curl.png")
        self.assertEqual(config.max_depth, 8)

    def test_invalid_settings(self):
        """Отвергает ошибочное значение каждого параметра."""
        cases = {
            "package": '"bad name"',
            "repository": '"file:///tmp/repository"',
            "test_mode": '"true"',
            "output": '"graph.svg"',
            "ascii_tree": '1',
            "max_depth": '-1',
        }
        source = EXAMPLE.read_text(encoding="utf-8").splitlines()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.toml"
            for name, invalid in cases.items():
                with self.subTest(name=name):
                    lines = [
                        f"{name} = {invalid}" if line.startswith(f"{name} = ")
                        else line
                        for line in source
                    ]
                    path.write_text("\n".join(lines), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, name):
                        load_config(path)
