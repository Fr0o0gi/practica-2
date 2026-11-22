import argparse
from dataclasses import fields
from pathlib import Path

from .config import load_config
from .graph import build_graph, dependency_source, download_order


def print_config(config):
    """Печатает настройки первого этапа в формате ключ=значение."""
    for field in fields(config):
        print(f"{field.name}={getattr(config, field.name)}")


def run_stage(config, stage):
    """Запускает проверку настроек, сбор или обход графа."""
    if stage == 1:
        print_config(config)
        return
    if stage == 2 and config.test_mode:
        raise ValueError("этап 2 использует реальный APKINDEX")
    direct = dependency_source(config)
    if stage == 2:
        print(f"Прямые зависимости {config.package}:")
        for name in direct(config.package):
            print(name)
        return
    graph = build_graph(config.package, direct, config.max_depth)
    if stage == 4:
        order, cycles = download_order(graph, config.package)
        print("Порядок загрузки: " + ", ".join(order))
        for source, target in cycles:
            print(f"Цикл: {source} -> {target}")
        return
    for name, dependencies in graph.items():
        print(f"{name}: {', '.join(dependencies) or '—'}")


def main():
    """Принимает путь к настройкам и запускает выбранный этап."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Alpine APK")
    parser.add_argument("config", type=Path, help="файл настроек TOML")
    parser.add_argument("--stage", type=int, choices=(1, 2, 3, 4), default=4)
    args = parser.parse_args()
    try:
        run_stage(load_config(args.config), args.stage)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
