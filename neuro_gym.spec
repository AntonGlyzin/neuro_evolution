from pathlib import Path

root_dir = Path.cwd()
entry_point = root_dir / 'app.py'

hiddenimports = [
    'tkinter',
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

    # wxPython и зависимости
    'wx',
    'wx.adv',
    'wx.core',
    'wx.gizmos',
    'wx.html2',
    'wx.lib',
    'wx.lib.agw',
    'wx.lib.agw.toasterbox',
    'wx.lib.agw.hyperlink',
    'wx.lib.agw.generictreectrl',
    'wx.lib.pubsub',
    'wx.lib.pubsub.core',
    'wx.lib.pubsub.core.kwargs',
    'wx.lib.pubsub.core.listener',
    'wx.lib.pubsub.core.publisher',
    'wx.lib.pubsub.utils',
    'wx.lib.pubsub.utils.publisher',
    
    # Matplotlib с wxPython бэкендом
    'matplotlib',
    'matplotlib.backends',
    'matplotlib.backends.backend_wxagg',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_wx',
    'matplotlib.figure',
    'matplotlib.pyplot',
    
    # Для multiprocessing
    'multiprocessing',
    'multiprocessing.context',
    'multiprocessing.queues',
    'multiprocessing.pool',
    'multiprocessing.managers',
    
    'services',
    'services.backend',
    'services.frontend',
    'neuro_gym',
]

icon_path = Path('./img/intelligence.ico')

# Анализ зависимостей
a = Analysis(
    [str(entry_point)],
    pathex=[str(root_dir)],
    binaries=[],
    datas=[
        (str(icon_path), 'img'),  # ← Копирует иконку в папку img внутри сборки
    ],
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
    name='NeuroEvolution',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # Использовать UPX для сжатия (если установлен)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Консольное приложение
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path),
)