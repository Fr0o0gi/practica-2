import re
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path
from urllib.parse import urlsplit


PACKAGE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9+_.-]*")
TEST_NAME = re.compile(r"[A-Z]")


@dataclass(frozen=True)
class Config:
    """Пользовательские настройки из одного файла TOML."""

    package: str
    repository: str
    test_mode: bool
    output: Path
    ascii_tree: bool
    max_depth: int


def require(values, name, expected_type):
    """Возвращает значение заданного типа или называет ошибочный ключ."""
    value = values[name]
    if type(value) is not expected_type:
        raise ValueError(f"{name}: нужен тип {expected_type.__name__}")
    return value


def validate_url(value):
    """Проверяет URL репозитория Alpine."""
    try:
        url = urlsplit(value)
        port = url.port
    except ValueError as error:
        raise ValueError("repository: некорректный URL") from error
    if url.scheme not in ("http", "https") or not url.hostname:
        raise ValueError("repository: нужен URL http:// или https://")
    if port == 0 or url.username is not None or url.query or url.fragment:
        raise ValueError("repository: укажите обычный URL индекса без входа")
    if any(char.isspace() for char in value):
        raise ValueError("repository: пробелы в URL недопустимы")


def load_config(path):
    """Читает TOML и проверяет все обязательные настройки."""
    with path.open("rb") as stream:
        values = tomllib.load(stream)
    expected = {field.name for field in fields(Config)}
    if set(values) != expected:
        missing = ", ".join(sorted(expected - values.keys())) or "—"
        extra = ", ".join(sorted(values.keys() - expected)) or "—"
        raise ValueError(f"TOML: пропущены {missing}; неизвестные: {extra}")
    test_mode = require(values, "test_mode", bool)
    ascii_tree = require(values, "ascii_tree", bool)
    package = require(values, "package", str)
    pattern = TEST_NAME if test_mode else PACKAGE_NAME
    if not pattern.fullmatch(package):
        raise ValueError("package: недопустимое имя пакета")
    repository = require(values, "repository", str)
    if test_mode:
        repository = str((path.parent / repository).resolve())
        if not Path(repository).is_file():
            raise ValueError("repository: тестовый файл не найден")
    else:
        validate_url(repository)
    output = (path.parent / require(values, "output", str)).resolve()
    if output.suffix.lower() != ".png" or output.is_dir():
        raise ValueError("output: нужен путь к файлу .png")
    max_depth = require(values, "max_depth", int)
    if max_depth < 0:
        raise ValueError("max_depth: нужна глубина от нуля")
    return Config(package, repository, test_mode, output, ascii_tree, max_depth)
