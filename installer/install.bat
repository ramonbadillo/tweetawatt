@echo off
echo Installing ElectroClient
start "" /wait python-2.7.10.msi

start "" /wait pyserial-2.7.win32.exe
exit /B
