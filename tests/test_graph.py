import unittest

from src.graph import build_graph, download_order


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

    def test_download_order(self):
        """Упорядочивает общую зависимость раньше обоих родителей."""
        graph = {"A": ("B", "C"), "B": ("D",), "C": ("D",), "D": ()}
        order, cycles = download_order(graph, "A")
        self.assertEqual(order, ["D", "B", "C", "A"])
        self.assertEqual(cycles, [])

    def test_download_order_on_cycle(self):
        """Возвращает каждую вершину один раз и показывает обратное ребро."""
        graph = {"A": ("B",), "B": ("A",)}
        order, cycles = download_order(graph, "A")
        self.assertEqual(order, ["B", "A"])
        self.assertEqual(cycles, [("B", "A")])
