import unittest

from src.visualize import ascii_tree, plantuml_text


class VisualizeTests(unittest.TestCase):
    """Проверяет полноту диаграммы и читаемость ASCII-дерева."""

    def test_cycle_and_shared_node(self):
        """Оставляет ссылки на циклы и узлы, уже показанные выше."""
        graph = {"A": ("B", "C"), "B": ("C",), "C": ("A",)}
        text = ascii_tree(graph, "A")
        self.assertIn("A [цикл]", text)
        self.assertIn("C [уже показан]", text)
        diagram = plantuml_text(graph, "A")
        self.assertIn('rectangle "A" as p0 #LightBlue', diagram)
        self.assertIn("p2 --> p0", diagram)
        self.assertEqual(diagram.count(" --> "), 4)
