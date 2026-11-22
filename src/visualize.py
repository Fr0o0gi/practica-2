import os
import subprocess
from pathlib import Path


PNG_HEADER = b"\x89PNG\r\n\x1a\n"
DEFAULT_JAR = Path(__file__).resolve().parents[1] / "tools" / "plantuml.jar"


def ascii_tree(graph, root):
    """Печатает дерево с метками повторных узлов и циклов."""
    lines = [root]
    seen = {root}
    active = {root}
    stack = [(root, "", iter(enumerate(graph[root])))]
    while stack:
        node, prefix, children = stack[-1]
        index, child = next(children, (0, None))
        if child is None:
            stack.pop()
            active.remove(node)
            continue
        last = index == len(graph[node]) - 1
        line = prefix + ("\\-- " if last else "+-- ") + child
        if child in active:
            lines.append(line + " [цикл]")
        elif child in seen:
            lines.append(line + " [уже показан]")
        else:
            lines.append(line)
            seen.add(child)
            active.add(child)
            indent = prefix + ("    " if last else "|   ")
            stack.append((child, indent, iter(enumerate(graph[child]))))
    return "\n".join(lines)


def plantuml_text(graph, root):
    """Создаёт прямоугольники пакетов и все рёбра графа."""
    aliases = {name: f"p{i}" for i, name in enumerate(graph)}
    lines = ["@startuml", "!pragma layout smetana", "skinparam shadowing false"]
    for name, alias in aliases.items():
        color = " #LightBlue" if name == root else ""
        lines.append(f'rectangle "{name}" as {alias}{color}')
    for source, dependencies in graph.items():
        for target in dependencies:
            lines.append(f"{aliases[source]} --> {aliases[target]}")
    return "\n".join([*lines, "@enduml", ""])


def render_png(diagram):
    """Передаёт PlantUML текст диаграммы и проверяет ответ PNG."""
    jar = Path(os.environ.get("PLANTUML_JAR", DEFAULT_JAR)).resolve()
    if not jar.is_file():
        raise ValueError(f"PlantUML JAR не найден: {jar}")
    command = [
        "java", "-Djava.awt.headless=true", "-jar", str(jar),
        "-charset", "UTF-8", "-tpng", "-failfast2", "-pipe",
    ]
    try:
        result = subprocess.run(
            command, input=diagram.encode("utf-8"),
            capture_output=True, timeout=45,
        )
    except subprocess.TimeoutExpired as error:
        message = "PlantUML не закончил генерацию за 45 секунд"
        raise ValueError(message) from error
    if result.returncode or not result.stdout.startswith(PNG_HEADER):
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"PlantUML: {detail or 'не удалось создать PNG'}")
    return result.stdout


def save_graph(config, graph):
    """Сохраняет исходник PlantUML и изображение рядом."""
    diagram = plantuml_text(graph, config.package)
    image = render_png(diagram)
    config.output.parent.mkdir(parents=True, exist_ok=True)
    source = config.output.with_suffix(".puml")
    source.write_text(diagram, encoding="utf-8")
    config.output.write_bytes(image)
    return source
