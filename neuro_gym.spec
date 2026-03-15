from pathlib import Path

root_dir = Path.cwd()
entry_point = root_dir / 'app.py'

hiddenimports = [
    'tkinter',
    'matplotlib.backends.backend_tkagg',
    'gymnasium.envs.classic_control',
    'gymnasium.envs.classic_control.continuous_mountain_car',
    'gymnasium.envs.classic_control.acrobot',
    'gymnasium.envs.classic_control.cartpole',
    'gymnasium.envs.classic_control.mountain_car',
    'gymnasium.envs.classic_control.pendulum',
    'gymnasium.envs.box2d',
    'gymnasium.envs.box2d.lunar_lander',
    'gymnasium.envs.box2d.bipedal_walker',
    'gymnasium.envs.box2d.car_racing',
    'gymnasium.envs.toy_text',
    'gymnasium.envs.toy_text.frozen_lake',
    'gymnasium.envs.toy_text.cliffwalking',
    'gymnasium.envs.toy_text.taxi',
    'gymnasium.envs.toy_text.blackjack',
    'gymnasium.envs.registration',
]

# Анализ зависимостей
a = Analysis(
    [str(entry_point)],
    pathex=[str(root_dir)],
    binaries=[],
    datas=[], # Не включаем никаких дополнительных данных
    hiddenimports=hiddenimports, # Укажите скрытые импорты, если нужны
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['environs', 'settings'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# Фильтрация: гарантированно убираем всё, что связано с environs и settings.py
a.datas = [
    x for x in a.datas 
    if not (
        x[0].startswith('environs') 
        or x[0].startswith('settings.py')
    )
]

# Дополнительно: если нужно исключить целые пакеты, можно так:
# a.pure = [x for x in a.pure if not x[0].startswith('environs.')]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='neuro_gym',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # Использовать UPX для сжатия (если установлен)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # Консольное приложение
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='./img/intelligence.ico',
)

# Если OneFile
# coll = COLLECT(exe, name='neuro_gym')