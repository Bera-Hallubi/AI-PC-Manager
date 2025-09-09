@echo off
echo AI PC Manager - Windows Setup
echo ============================

REM Check if running as administrator
net session >nul 2>&1
if errorlevel 1 (
    echo This script requires administrator privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

echo Installing AI PC Manager...
echo.

REM Create installation directory
set INSTALL_DIR=%PROGRAMFILES%\AI PC Manager
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy files
echo Copying application files...
xcopy /E /I /Y "dist\AI_PC_Manager\*" "%INSTALL_DIR%\"

REM Create desktop shortcut
echo Creating desktop shortcut...
set DESKTOP=%USERPROFILE%\Desktop
echo [InternetShortcut] > "%DESKTOP%\AI PC Manager.url"
echo URL=file:///%INSTALL_DIR%\AI_PC_Manager.exe >> "%DESKTOP%\AI PC Manager.url"
echo IconFile=%INSTALL_DIR%\AI_PC_Manager.exe >> "%DESKTOP%\AI PC Manager.url"
echo IconIndex=0 >> "%DESKTOP%\AI PC Manager.url"

REM Create start menu shortcut
echo Creating start menu shortcut...
set START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
if not exist "%START_MENU%\AI PC Manager" mkdir "%START_MENU%\AI PC Manager"

echo [InternetShortcut] > "%START_MENU%\AI PC Manager\AI PC Manager.url"
echo URL=file:///%INSTALL_DIR%\AI_PC_Manager.exe >> "%START_MENU%\AI PC Manager\AI PC Manager.url"
echo IconFile=%INSTALL_DIR%\AI_PC_Manager.exe >> "%START_MENU%\AI PC Manager\AI_PC_Manager.exe"
echo IconIndex=0 >> "%START_MENU%\AI PC Manager\AI PC Manager.url"

REM Create uninstaller
echo Creating uninstaller...
echo @echo off > "%INSTALL_DIR%\uninstall.bat"
echo echo Uninstalling AI PC Manager... >> "%INSTALL_DIR%\uninstall.bat"
echo taskkill /f /im AI_PC_Manager.exe 2^>nul >> "%INSTALL_DIR%\uninstall.bat"
echo timeout /t 2 /nobreak ^>nul >> "%INSTALL_DIR%\uninstall.bat"
echo rmdir /s /q "%INSTALL_DIR%" >> "%INSTALL_DIR%\uninstall.bat"
echo del "%DESKTOP%\AI PC Manager.url" >> "%INSTALL_DIR%\uninstall.bat"
echo rmdir /s /q "%START_MENU%\AI PC Manager" >> "%INSTALL_DIR%\uninstall.bat"
echo echo AI PC Manager has been uninstalled. >> "%INSTALL_DIR%\uninstall.bat"
echo pause >> "%INSTALL_DIR%\uninstall.bat"

REM Add to Windows registry for uninstall
echo Adding to Windows registry...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\AI PC Manager" /v "DisplayName" /t REG_SZ /d "AI PC Manager" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\AI PC Manager" /v "UninstallString" /t REG_SZ /d "%INSTALL_DIR%\uninstall.bat" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\AI PC Manager" /v "InstallLocation" /t REG_SZ /d "%INSTALL_DIR%" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\AI PC Manager" /v "DisplayVersion" /t REG_SZ /d "1.0.0" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\AI PC Manager" /v "Publisher" /t REG_SZ /d "AI PC Manager" /f

echo.
echo ✅ Installation completed successfully!
echo.
echo AI PC Manager has been installed to: %INSTALL_DIR%
echo Desktop shortcut created
echo Start menu shortcut created
echo.
echo You can now launch AI PC Manager from:
echo • Desktop shortcut
echo • Start menu
echo • %INSTALL_DIR%\AI_PC_Manager.exe
echo.
echo To uninstall, run: %INSTALL_DIR%\uninstall.bat
echo.
pause
