import json
from pathlib import Path

from .apk import load_apk
from .config import TEST_NAME


def unique_keys(pairs):
    """Не допускает дублирование имён пакетов в JSON."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"повторяющийся пакет {key!r}")
        result[key] = value
    return result


def load_test_graph(path):
    """Читает граф A–Z и проверяет типы, имена и ссылки."""
    raw = json.loads(path.read_text(encoding="utf-8-sig"),
                     object_pairs_hook=unique_keys)
    if not isinstance(raw, dict):
        raise ValueError("тестовый JSON должен содержать объект")
    graph = {}
    for name, dependencies in raw.items():
        if not TEST_NAME.fullmatch(name) or not isinstance(dependencies, list):
            raise ValueError(f"{name!r}: нужен пакет A–Z и список зависимостей")
        for dependency in dependencies:
            if not isinstance(dependency, str) or dependency not in raw:
                raise ValueError(f"{name!r}: неизвестный пакет {dependency!r}")
        graph[name] = tuple(dict.fromkeys(dependencies))
    return graph


def dependency_source(config):
    """Отдаёт функцию чтения соседей из Alpine или тестового JSON."""
    if config.test_mode:
        graph = load_test_graph(Path(config.repository))
        if config.package not in graph:
            raise ValueError(f"нет тестового пакета {config.package!r}")
        return graph.__getitem__
    repository = load_apk(config.repository)
    if config.package not in repository.packages:
        raise ValueError(f"пакет {config.package!r} отсутствует в индексе")
    return repository.direct


def build_graph(root, direct, max_depth):
    """Обходит граф явным стеком и учитывает кратчайшую найденную глубину."""
    stack = [(root, 0)]
    graph = {}
    depths = {}
    while stack:
        name, depth = stack.pop()
        if depth >= depths.get(name, max_depth + 1):
            continue
        depths[name] = depth
        if depth == max_depth:
            graph.setdefault(name, ())
            continue
        dependencies = direct(name)
        graph[name] = dependencies
        stack.extend((child, depth + 1) for child in reversed(dependencies))
    return graph
