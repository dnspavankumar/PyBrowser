@echo off
echo Building PavanBrowser for Windows...
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Build the executable
echo.
echo Building executable...
pyinstaller PavanBrowser.spec --clean

echo.
echo Build complete! Executable is in the dist/PavanBrowser folder
pause
