@echo off
setlocal enabledelayedexpansion

for /f "tokens=2 delims== " %%A in (patchValue.txt) do set patch=%%A
set /a patch+=1
echo patch = %patch% > patchValue.txt

python main.py
pause
