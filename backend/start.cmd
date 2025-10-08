@REM @echo off

@REM echo.
@REM echo Restoring backend python packages
@REM echo.
@REM call python -m pip install -r requirements.txt
@REM if "%errorlevel%" neq "0" (
@REM     echo Failed to restore backend python packages
@REM     exit /B %errorlevel%
@REM )

python -m uvicorn open_webui.main:app --port 8080 --host 0.0.0.0 --forwarded-allow-ips '*' --reload
if "%errorlevel%" neq "0" (    
    echo Failed to start backend    
    exit
)
 