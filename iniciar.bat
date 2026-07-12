@echo off
title Gerador de Legendas SRT - Ativo
echo ====================================================
echo    INICIANDO O GERADOR DE LEGENDAS LOCAL
echo    (Mantenha esta janela aberta durante o uso)
echo ====================================================
echo.

if not exist venv (
    echo [ERRO] Ambiente nao instalado! 
    echo Por favor, execute o arquivo INSTALAR.bat primeiro.
    echo.
    pause
    exit
)

:: Ativa o ambiente isolado e roda o app
call venv\Scripts\activate
python app_legendas.py

:: Desativa o ambiente virtual ao encerrar o app
call venv\Scripts\deactivate
echo.
echo Aplicação encerrada com sucesso.
timeout /t 3 >nul