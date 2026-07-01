@echo off
setlocal

:: Verifica se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale em https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Cria o ambiente virtual na primeira vez
if not exist ".venv" (
    echo [setup] Criando ambiente virtual...
    python -m venv .venv
)

:: Ativa o ambiente virtual
call .venv\Scripts\activate.bat

:: Instala dependencias se necessario
python -c "import piper" >nul 2>&1
if errorlevel 1 (
    echo [setup] Instalando dependencias...
    pip install -r requirements.txt
    echo.
)

:: Roda o script com os argumentos passados
if "%~1"=="" (
    python say.py --demo
) else (
    python say.py %*
)

endlocal
