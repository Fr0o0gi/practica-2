import unittest

from src.graph import build_graph


class GraphTests(unittest.TestCase):
    """Проверяет циклы, глубину и повторный приход более коротким путём."""

    def test_cycle_and_limit(self):
        """Сохраняет обратное ребро и завершает обход цикла."""
        source = {"A": ("B",), "B": ("C",), "C": ("A",)}
        self.assertEqual(build_graph("A", source.__getitem__, 3), source)
        expected = {"A": ("B",), "B": ()}
        self.assertEqual(build_graph("A", source.__getitem__, 1), expected)

    def test_shorter_path_expands_node(self):
        """Раскрывает узел, когда второй путь оставляет запас глубины."""
        source = {"A": ("B", "C"), "B": ("C",), "C": ("D",), "D": ()}
        self.assertEqual(build_graph("A", source.__getitem__, 2), source)

    def test_stack(self):
        """Проходит цепочку длиннее стандартного предела рекурсии."""
        size = 1500
        source = {str(i): (str(i + 1),) for i in range(size)}
        result = build_graph("0", source.__getitem__, size)
        self.assertEqual(len(result), size + 1)
        self.assertEqual(result[str(size)], ())
