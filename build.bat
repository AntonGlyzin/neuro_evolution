@echo off
if not exist env\ (
    echo Creating virtual environm...
    python -m venv env
	call .\env\Scripts\activate.bat
	pip install -r requirements.txt
	pyinstaller neuro_gym.spec
) else (
    call .\env\Scripts\activate.bat
	pyinstaller neuro_gym.spec
)