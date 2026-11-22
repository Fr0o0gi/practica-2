import gzip
import tarfile
import unittest
from io import BytesIO

from src.apk import ApkRepository, package_records, read_index


INDEX = """P:app
V:1.0-r0
D:so:libdemo.so.1 helper>=2.0 !conflict

P:libdemo
V:1.0-r0
p:so:libdemo.so.1

P:helper
V:2.0-r1
"""


class ApkTests(unittest.TestCase):
    """Проверяет APKINDEX, виртуальные и версионные зависимости."""

    def test_signed_layout(self):
        """Читает две последовательные gzip-части Alpine."""
        buffer = BytesIO()
        files = ((".SIGN", b"signature"), ("APKINDEX", INDEX.encode()))
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            for name, data in files:
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, BytesIO(data))
        contents = buffer.getvalue()
        signature, index = contents[:1024], contents[1024:]
        signed_parts = gzip.compress(signature) + gzip.compress(index)
        self.assertEqual(read_index(signed_parts), INDEX)

    def test_real_package_names(self):
        """Подставляет поставщика и исключает конфликт из списка рёбер."""
        repository = ApkRepository(package_records(INDEX))
        self.assertEqual(repository.direct("app"), ("libdemo", "helper"))
        self.assertEqual(repository.resolve("helper~2.0"), "helper")
        with self.assertRaises(ValueError):
            repository.resolve("helper>=3.0")
