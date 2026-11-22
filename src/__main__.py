import argparse
from dataclasses import fields
from pathlib import Path

from .apk import load_apk
from .config import load_config


def print_config(config):
    """Печатает настройки первого этапа в формате ключ=значение."""
    for field in fields(config):
        print(f"{field.name}={getattr(config, field.name)}")


def main():
    """Принимает путь к настройкам и запускает выбранный этап."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Alpine APK")
    parser.add_argument("config", type=Path, help="файл настроек TOML")
    parser.add_argument("--stage", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.stage == 1:
            print_config(config)
        else:
            if config.test_mode:
                raise ValueError("этап 2 использует реальный APKINDEX")
            repository = load_apk(config.repository)
            print(f"Прямые зависимости {config.package}:")
            for name in repository.direct(config.package):
                print(name)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
