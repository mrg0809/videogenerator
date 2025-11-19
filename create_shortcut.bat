@echo off
REM ============================================================
REM Video Generator - Crear Acceso Directo en el Escritorio
REM ============================================================
REM Este script crea un acceso directo en el escritorio de Windows
REM para iniciar facilmente Video Generator
REM ============================================================

echo.
echo ============================================================
echo   Crear Acceso Directo en el Escritorio
echo ============================================================
echo.

REM Obtiene el directorio actual
set "SCRIPT_DIR=%~dp0"
set "BATCH_FILE=%SCRIPT_DIR%start_windows.bat"

REM Verifica que el archivo start_windows.bat existe
if not exist "%BATCH_FILE%" (
    echo ERROR: No se encuentra el archivo start_windows.bat
    echo.
    echo Asegurate de ejecutar este script desde el directorio
    echo del proyecto Video Generator.
    echo.
    pause
    exit /b 1
)

REM Obtiene la ruta del escritorio del usuario
set "DESKTOP=%USERPROFILE%\Desktop"

REM Nombre del acceso directo
set "SHORTCUT_NAME=Video Generator.lnk"
set "SHORTCUT_PATH=%DESKTOP%\%SHORTCUT_NAME%"

echo Creando acceso directo en: %DESKTOP%
echo.

REM Crea un script VBS temporal para crear el acceso directo
set "VBS_SCRIPT=%TEMP%\create_shortcut.vbs"

(
echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo sLinkFile = "%SHORTCUT_PATH%"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
echo oLink.TargetPath = "%BATCH_FILE%"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
echo oLink.Description = "Iniciar Video Generator - Generador de Videos"
echo oLink.IconLocation = "%SystemRoot%\System32\shell32.dll,165"
echo oLink.Save
) > "%VBS_SCRIPT%"

REM Ejecuta el script VBS
cscript //nologo "%VBS_SCRIPT%"

REM Elimina el script VBS temporal
del "%VBS_SCRIPT%"

if exist "%SHORTCUT_PATH%" (
    echo.
    echo ============================================================
    echo   EXITO: Acceso directo creado correctamente
    echo ============================================================
    echo.
    echo El acceso directo "Video Generator" ha sido creado en
    echo tu escritorio.
    echo.
    echo Para usar Video Generator:
    echo 1. Haz doble clic en el acceso directo del escritorio
    echo 2. Espera a que se abra el navegador
    echo 3. Comienza a generar tus videos
    echo.
    echo NOTA: La primera vez que lo uses, puede tardar mas tiempo
    echo mientras se descargan los modelos de IA necesarios.
    echo.
) else (
    echo.
    echo ERROR: No se pudo crear el acceso directo
    echo.
    echo Intenta ejecutar este script como Administrador.
    echo.
)

pause
