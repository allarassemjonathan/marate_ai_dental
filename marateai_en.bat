@echo off
setlocal EnableDelayedExpansion

:: Define config file path
set "CONFIG_FILE=%USERPROFILE%\marate_config.txt"

:: Check if config file exists
if exist "%CONFIG_FILE%" (
    echo Loading paths from config...
    for /f "tokens=1,* delims==" %%A in (%CONFIG_FILE%) do (
        set "%%A=%%B"
    )
) else (
    call :GetPaths
)

echo Installing requirements...
"%PYTHON_PATH%" -m pip install -r "%LEETCODE_PATH%\requirements.txt"

:: Get local IP address
FOR /F "tokens=2 delims=:" %%A IN ('ipconfig ^| findstr /R "IPv4.*"') DO (
    set "LOCAL_IP=%%A"
    goto :strip_and_continue
)

:strip_and_continue
set "LOCAL_IP=%LOCAL_IP: =%"
set "FLASK_URL=http://%LOCAL_IP%:5000"

echo.
echo ---------------------------------------
echo Marate AI will run at: %FLASK_URL%
echo ---------------------------------------

:: Launch a delayed browser in a parallel process
start "" cmd /c "timeout /t 5 >nul && start %FLASK_URL%"

echo Starting Marate AI web app...
"%PYTHON_PATH%" -m flask --app "%LEETCODE_PATH%\app.py" run --host=0.0.0.0

echo Productx app launched.
pause
exit /b

:GetPaths
echo First-time setup:
set /p "LEETCODE_PATH=Enter full path to LeetCode folder: "
set /p "PYTHON_PATH=Enter full path to Python executable: "

echo LEETCODE_PATH=%LEETCODE_PATH%> "%CONFIG_FILE%"
echo PYTHON_PATH=%PYTHON_PATH%>> "%CONFIG_FILE%"
exit /b
