import argparse
from dataclasses import fields
from pathlib import Path

from .config import load_config


def print_config(config):
    """Печатает настройки первого этапа в формате ключ=значение."""
    for field in fields(config):
        print(f"{field.name}={getattr(config, field.name)}")


def main():
    """Принимает путь к настройкам и запускает выбранный этап."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Alpine APK")
    parser.add_argument("config", type=Path, help="файл настроек TOML")
    parser.add_argument("--stage", type=int, choices=(1,), default=1)
    args = parser.parse_args()
    try:
        print_config(load_config(args.config))
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
