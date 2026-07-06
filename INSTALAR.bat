@echo off
title INSTALADOR - Gerador de Legendas
echo ====================================================
echo    CONFIGURANDO O AMBIENTE (PRIMEIRA EXECUCAO)
echo ====================================================
echo.

:: Verifica se o Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] O Python nao foi encontrado neste computador!
    echo Por favor, instale o Python e marque a opcao Add Python to PATH.
    echo.
    pause
    exit
)

echo [1/3] Criando o Ambiente Virtual isolado (VENV)...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao criar o ambiente virtual.
    pause
    exit
)

echo [2/3] Ativando o ambiente virtual...
call venv\Scripts\activate

echo [3/3] Instalando dependencias e suporte a GPU...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ====================================================
echo    INSTALACAO CONCLUIDA COM SUCESSO!
echo    Agora voce pode usar o arquivo INICIAR.bat
echo ====================================================
echo.
pause