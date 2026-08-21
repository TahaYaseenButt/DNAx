@echo off
echo =======================================================
echo     DNAx Laboratory Suite - Desktop Build Pipeline
echo =======================================================
echo.

echo [1/3] Compiling React Vite UI Frontend...
cd ui
call npm.cmd run build
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] React UI build failed!
    cd ..
    pause
    exit /b %ERRORLEVEL%
)
cd ..
echo [OK] React UI compiled into ui/dist/

echo.
echo [2/3] Bundling Python Engine + React UI into Standalone .exe...
python -m PyInstaller --noconfirm DNAx_Webview.spec
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller bundling failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] Build Complete!
echo Standalone Executable created at: dist\DNAx_Lab_Pro.exe
echo You can run or distribute dist\DNAx_Lab_Pro.exe to any fresh Windows PC.
echo =======================================================
pause
