from __future__ import annotations
from pathlib import Path
import sys
import importlib
import multiprocessing as mp

if getattr(sys, 'frozen', False):
    base_path = Path(sys.executable).parent
else:
    base_path = Path(__file__).parent
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))

importlib.import_module('environs')
import services
from neuro_gym import RootService

settings = importlib.import_module('settings')


if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    mp.freeze_support()
    root = RootService()
    root.start_services()
    root.join()
    root.close()
    sys.exit(0)