@echo off
REM ============================================================
REM Video Generator - Script de Inicio para Windows
REM ============================================================
REM Este script inicia el servidor Flask y abre el navegador
REM automaticamente en la interfaz web de Video Generator
REM ============================================================

echo.
echo ============================================================
echo      VIDEO GENERATOR - Iniciando Servidor
echo ============================================================
echo.

REM Guarda el directorio actual
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Verifica si Python esta instalado
echo [1/5] Verificando instalacion de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo.
    echo Por favor, instala Python 3.8 o superior desde:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Durante la instalacion, marca la opcion
    echo "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
python --version
echo OK - Python encontrado
echo.

REM Verifica si el entorno virtual existe
echo [2/5] Verificando entorno virtual...
if not exist "venv\Scripts\activate.bat" (
    echo Entorno virtual no encontrado. Creando...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: No se pudo crear el entorno virtual
        echo.
        pause
        exit /b 1
    )
    echo OK - Entorno virtual creado
) else (
    echo OK - Entorno virtual encontrado
)
echo.

REM Activa el entorno virtual
echo [3/5] Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo.
    echo ERROR: No se pudo activar el entorno virtual
    echo.
    pause
    exit /b 1
)
echo OK - Entorno virtual activado
echo.

REM Verifica e instala dependencias
echo [4/5] Verificando dependencias...
set DEPS_INSTALLED=0
python -c "import flask" 2>nul
if %errorlevel% equ 0 set DEPS_INSTALLED=1

if %DEPS_INSTALLED% equ 0 (
    echo Instalando dependencias (esto puede tomar varios minutos)...
    echo.
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: No se pudieron instalar las dependencias
        echo.
        echo Verifica tu conexion a internet y que el archivo
        echo requirements.txt exista en el directorio actual.
        echo.
        pause
        exit /b 1
    )
    echo.
    echo OK - Dependencias instaladas correctamente
    echo.
    echo NOTA: La primera vez que uses la aplicacion, rembg
    echo descargara automaticamente el modelo de IA (varios cientos de MB).
    echo Esto puede tardar unos minutos.
    echo.
) else (
    echo OK - Dependencias ya instaladas
)
echo.

REM Verifica FFmpeg
echo Verificando FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ADVERTENCIA: FFmpeg no esta instalado o no esta en el PATH
    echo.
    echo FFmpeg es requerido para procesar videos.
    echo Descargalo desde: https://ffmpeg.org/download.html
    echo.
    echo Despues de descargar:
    echo 1. Extrae el archivo ZIP
    echo 2. Copia la carpeta 'bin' a C:\ffmpeg\bin
    echo 3. Anade C:\ffmpeg\bin al PATH del sistema
    echo.
    echo Presiona una tecla para continuar de todas formas...
    pause >nul
) else (
    echo OK - FFmpeg encontrado
)
echo.

REM Inicia el servidor Flask en segundo plano
echo [5/5] Iniciando servidor Flask...
echo.
echo ============================================================
echo  El servidor se esta iniciando en http://localhost:5000
echo ============================================================
echo.
echo El navegador se abrira automaticamente en unos segundos...
echo.
echo IMPORTANTE:
echo - NO CIERRES esta ventana mientras uses la aplicacion
echo - Para detener el servidor, presiona Ctrl+C en esta ventana
echo - Los videos generados se guardaran en la carpeta 'videos'
echo.
echo ============================================================
echo.

REM Espera 3 segundos antes de abrir el navegador
timeout /t 3 /nobreak >nul

REM Abre el navegador en la interfaz
start http://localhost:5000

REM Inicia el servidor Flask (esto bloqueara hasta que se cierre)
python app.py

REM Si llegamos aqui, el servidor se cerro
echo.
echo ============================================================
echo  Servidor detenido
echo ============================================================
echo.
pause