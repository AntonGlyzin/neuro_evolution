# mkdocs.py
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Импортируем и запускаем mkdocs
from mkdocs.__main__ import cli

if __name__ == "__main__":
    cli()