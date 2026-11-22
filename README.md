# Граф зависимостей Alpine Linux

Практическая работа №2 по конфигурационному управлению, вариант 23.
Реализованы этапы 1, 2, 3 и 5.
Для запуска нужен Python 3.11 или новее. Команды выполняются из корня
репозитория.

## Этап 1. Настройки

```powershell
.\run.bat examples/alpine.toml --stage 1
```

На Linux или macOS вместо `.\run.bat` используйте `python -m src`.
Пользовательские настройки читаются из файла TOML.

| Ключ | Назначение |
| --- | --- |
| `package` | Имя анализируемого пакета Alpine или буква A–Z в тестовом режиме |
| `repository` | URL репозитория с архитектурой или путь к локальному JSON |
| `test_mode` | Использовать локальный тестовый граф |
| `output` | Путь к выходному файлу PNG |
| `ascii_tree` | Вывести граф в терминал в виде дерева |
| `max_depth` | Максимальная глубина. Корневой пакет имеет глубину 0 |

Относительные пути вычисляются от папки TOML. Первая команда выводит все
шесть параметров в формате ключ=значение. Проверка ошибок конфигурации
запускается командой `python -m unittest discover -s tests`.

## Этап 2. Прямые зависимости APK

```powershell
.\run.bat examples/alpine.toml --stage 2
```

Команда загружает `APKINDEX.tar.gz` и читает запись пакета из текстового
индекса. Поле `D` задаёт зависимости. Для имён вида `so:libcurl.so.4`
программа ищет пакет, который объявляет это имя в поле `p`.
Настройка `repository` принимает URL каталога с архитектурой
(например, `x86_64`) или ссылку на сам индекс.

## Этап 3. Обход графа

```powershell
.\run.bat examples/test.toml --stage 3
.\run.bat examples/cycle.toml --stage 3
.\run.bat examples/depth.toml --stage 3
```

Итеративный DFS хранит пакеты в стеке. При повторном посещении узел
раскрывается только если новый путь короче уже найденного. Поэтому
ребро цикла видно в графе, а обход заканчивается. При глубине 1 видны
корень и его прямые зависимости. При глубине 0 виден только корень.

Формат тестового JSON — объект, где каждому имени A–Z соответствует
массив прямых зависимостей. Каждая указанная буква должна быть объявлена.

## Этап 5. PlantUML, PNG и ASCII

Нужны Java и [PlantUML JAR](https://github.com/plantuml/plantuml/releases).
Положите JAR в `tools/plantuml.jar` или укажите путь в переменной
окружения `PLANTUML_JAR`. Встроенный движок Smetana компонует граф.

```powershell
New-Item -ItemType Directory -Path tools -Force | Out-Null
Invoke-WebRequest -Uri https://github.com/plantuml/plantuml/releases/download/v1.2026.10/plantuml-java8-1.2026.10.jar -OutFile tools/plantuml.jar
.\run.bat examples/alpine.toml
.\run.bat examples/jq.toml
.\run.bat examples/zlib.toml
```

Для `curl`, `jq` и `zlib` создаются файлы PNG и PlantUML в папке `output/`.
При `ascii_tree = true` в терминале также выводится дерево с отметками
циклов и общих зависимостей. Для проверки без интернета используйте
`.\run.bat examples/test.toml`.

Штатный `apk dot` используется отдельно для сверки. Результаты приведены
в [отчёте о сравнении](docs/comparison.md).

### Функции

- `load_config` читает TOML, `require` и `validate_url` проверяют параметры.
- `load_apk` загружает индекс. `index_url` строит ссылку, `read_index` читает
  архив, `package_records` разбирает записи.
- `parse_dependency` разделяет имя и ограничение, `version_key` и `matches`
  проверяют версии. `ApkRepository.resolve` выбирает пакет, а
  `ApkRepository.direct` возвращает прямые зависимости.
- `load_test_graph` читает JSON с проверкой повтора ключей через `unique_keys`.
  `dependency_source` подключает тестовый граф или Alpine.
- `build_graph` строит граф итеративным DFS.
- `plantuml_text` строит диаграмму, `render_png` запускает PlantUML,
  `save_graph` записывает исходник и изображение. `ascii_tree` строит дерево.
- `main` читает параметры запуска, `run_stage` выбирает операцию,
  `print_config` показывает настройки первого этапа.

Анализ охватывает один индекс APK v2. Программа разрешает зависимости
и виртуальные имена из этого индекса. Штатный решатель APK дополнительно
учитывает состояние системы, конфликты и правила автоматической установки.
