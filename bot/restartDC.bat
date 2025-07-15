@echo off
echo Closing Discord...

taskkill /IM discord.exe /F >nul 2>&1

echo Waiting 2 seconds...
timeout /T 2 /NOBREAK >nul

echo Starting Discord...
start "" "%LOCALAPPDATA%\Discord\Update.exe" --processStart Discord.exe

echo Done.
