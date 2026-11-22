import re
import tarfile
from collections import defaultdict
from dataclasses import dataclass
from gzip import GzipFile
from io import BytesIO
from urllib.request import urlopen

from .config import PACKAGE_NAME


INDEX_NAME = "APKINDEX.tar.gz"
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_INDEX_BYTES = 64 * 1024 * 1024
DEPENDENCY = re.compile(r"(!?)([^<>=~!]+)([<>=~]*)(.*)")
VERSION = re.compile(
    r"(\d+(?:\.\d+)*)([a-z]?)((?:_[a-z]+\d*)*)"
    r"(?:~([0-9a-f]+))?(?:-r(\d+))?"
)
SUFFIXES = {
    name: index - 4
    for index, name in enumerate(
        ("alpha", "beta", "pre", "rc", "", "cvs", "svn", "git", "hg", "p")
    )
}


@dataclass(frozen=True)
class Package:
    """Поля APKINDEX, нужные для разрешения зависимостей."""

    name: str
    version: str
    depends: tuple[str, ...]
    provides: tuple[str, ...]
    priority: int


def index_url(repository):
    """Строит ссылку на индекс для каталога выбранной архитектуры."""
    if repository.endswith("/" + INDEX_NAME):
        return repository
    return f"{repository.rstrip('/')}/{INDEX_NAME}"


def read_index(archive_bytes):
    """Читает APKINDEX из tar.gz прямо в память."""
    with GzipFile(fileobj=BytesIO(archive_bytes)) as gzip_file:
        contents = gzip_file.read(MAX_INDEX_BYTES + 1)
    if len(contents) > MAX_INDEX_BYTES:
        raise ValueError("слишком большой APKINDEX")
    with tarfile.open(fileobj=BytesIO(contents), mode="r:") as archive:
        for member in archive:
            if member.name == "APKINDEX" and member.isfile():
                with archive.extractfile(member) as stream:
                    return stream.read().decode("utf-8")
    raise ValueError("в архиве отсутствует APKINDEX")


def package_records(index):
    """Разбирает записи индекса, отделённые пустыми строками."""
    for block in re.split(r"\r?\n[ \t]*\r?\n", index.strip()):
        fields = dict(line.split(":", 1) for line in block.splitlines())
        if "P" in fields and "V" in fields:
            if not PACKAGE_NAME.fullmatch(fields["P"]):
                raise ValueError(f"некорректное имя пакета: {fields['P']!r}")
            yield Package(
                fields["P"], fields["V"], tuple(fields.get("D", "").split()),
                tuple(fields.get("p", "").split()), int(fields.get("k", "0")),
            )


def version_key(value):
    """Выделяет числовые части, суффиксы и ревизию версии APK."""
    match = VERSION.fullmatch(value)
    if not match:
        raise ValueError(f"неподдерживаемая версия APK: {value}")
    core, letter, suffix, commit, revision = match.groups()
    parts = tuple(int(digit) for digit in core.split("."))
    suffixes = tuple(
        (SUFFIXES[name], int(number or "0"))
        for name, number in re.findall(r"_([a-z]+)(\d*)", suffix)
    )
    return parts, letter, suffixes + ((0, 0),), commit or "", int(revision or 0)


def parse_dependency(token):
    """Разделяет имя зависимости, оператор и версию."""
    match = DEPENDENCY.fullmatch(token)
    if not match:
        raise ValueError(f"некорректная зависимость APK: {token}")
    conflict, name, operator, version = match.groups()
    if bool(operator) != bool(version):
        raise ValueError(f"некорректная версия зависимости: {token}")
    return conflict, name, operator, version


def matches(version, operator, target):
    """Проверяет ограничение версии у пакета или предоставляемого имени."""
    if not operator:
        return True
    if not version:
        return False
    if operator == "><":
        return False
    prefix = re.escape(target) + r"(?=$|[._-])"
    if "~" in operator and re.match(prefix, version):
        return True
    actual, expected = version_key(version), version_key(target)
    if actual == expected:
        return "=" in operator or "~" in operator
    return "<" in operator if actual < expected else ">" in operator


class ApkRepository:
    """Ищет пакеты и их поставщиков в загруженном индексе."""

    def __init__(self, packages):
        self.packages = {}
        self.providers = defaultdict(list)
        for package in packages:
            old = self.packages.get(package.name)
            if old is None or (
                version_key(package.version) > version_key(old.version)
            ):
                self.packages[package.name] = package
        for package in self.packages.values():
            for provided in package.provides:
                _, name, _, version = parse_dependency(provided)
                self.providers[name].append((package, version))
        if not self.packages:
            raise ValueError("индекс APK не содержит пакетов")

    def resolve(self, token):
        """Возвращает имя пакета, удовлетворяющего положительной зависимости."""
        _, name, operator, version = parse_dependency(token)
        package = self.packages.get(name)
        if package and matches(package.version, operator, version):
            return name
        options = [
            (provider, provided_version)
            for provider, provided_version in self.providers.get(name, ())
            if matches(provided_version, operator, version)
        ]
        if not options:
            raise ValueError(f"пакет для зависимости {token!r} не найден")
        provider, _ = max(
            options,
            key=lambda option: (
                option[0].priority,
                version_key(option[1] or option[0].version),
                option[0].name,
            ),
        )
        return provider.name

    def direct(self, name):
        """Возвращает прямые зависимости как имена пакетов."""
        if name not in self.packages:
            raise ValueError(f"пакет {name!r} отсутствует в индексе")
        dependencies = (
            self.resolve(token)
            for token in self.packages[name].depends
            if not token.startswith("!")
        )
        return tuple(dict.fromkeys(dependencies))


def load_apk(repository):
    """Загружает и разбирает опубликованный Alpine APKINDEX."""
    uri = index_url(repository)
    try:
        with urlopen(uri, timeout=20) as response:
            contents = response.read(MAX_ARCHIVE_BYTES + 1)
        if len(contents) > MAX_ARCHIVE_BYTES:
            raise ValueError("слишком большой архив APKINDEX")
        return ApkRepository(package_records(read_index(contents)))
    except (OSError, EOFError, tarfile.TarError, ValueError) as error:
        raise ValueError(f"не удалось прочитать {uri}: {error}") from error
